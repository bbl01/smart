"""
Скрипт обучения/дообучения модели распознавания лиц
на пользовательском датасете (студенты/сотрудники).

Использует ArcFace loss + ResNet backbone через InsightFace.
"""
import argparse
import os
import sys
from pathlib import Path

import numpy as np
from loguru import logger


def prepare_dataset(photos_dir: str, output_dir: str):
    """
    Подготовка датасета из папки с фотографиями.

    Ожидаемая структура:
    photos_dir/
        student_001/
            photo_1.jpg
            photo_2.jpg
        student_002/
            photo_1.jpg
        ...

    Выходной формат:
    output_dir/
        embeddings.npy   — матрица (N, 512)
        labels.npy       — массив меток (N,)
        id_map.json      — маппинг label_idx -> person_id
    """
    import json
    try:
        from insightface.app import FaceAnalysis
        import cv2
    except ImportError:
        logger.error("Установите insightface: pip install insightface")
        sys.exit(1)

    photos_path = Path(photos_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Загрузка InsightFace модели...")
    app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    app.prepare(ctx_id=-1, det_size=(640, 640))

    embeddings_list = []
    labels_list = []
    id_map = {}

    person_dirs = [d for d in photos_path.iterdir() if d.is_dir()]
    logger.info(f"Найдено {len(person_dirs)} персон")

    for label_idx, person_dir in enumerate(sorted(person_dirs)):
        person_id = person_dir.name
        id_map[label_idx] = person_id

        photo_files = list(person_dir.glob("*.jpg")) + \
                      list(person_dir.glob("*.jpeg")) + \
                      list(person_dir.glob("*.png"))

        person_embeddings = []
        for photo_path in photo_files:
            img = cv2.imread(str(photo_path))
            if img is None:
                continue

            faces = app.get(img)
            if not faces:
                logger.warning(f"Лицо не найдено: {photo_path}")
                continue

            # Берём лицо с максимальным bbox
            face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
            emb = face.embedding

            # L2 нормализация
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm

            person_embeddings.append(emb)

        if person_embeddings:
            # Усредняем эмбеддинги персоны для большей устойчивости
            mean_emb = np.mean(person_embeddings, axis=0)
            mean_norm = np.linalg.norm(mean_emb)
            if mean_norm > 0:
                mean_emb = mean_emb / mean_norm

            embeddings_list.append(mean_emb)
            labels_list.append(label_idx)
            logger.success(f"  {person_id}: {len(person_embeddings)} фото обработано")
        else:
            logger.warning(f"  {person_id}: нет валидных фото, пропускаем")

    if not embeddings_list:
        logger.error("Нет данных для сохранения")
        sys.exit(1)

    # Сохраняем
    embeddings_matrix = np.vstack(embeddings_list).astype(np.float32)
    labels_array = np.array(labels_list, dtype=np.int32)

    np.save(output_path / "embeddings.npy", embeddings_matrix)
    np.save(output_path / "labels.npy", labels_array)

    with open(output_path / "id_map.json", "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)

    logger.success(f"\n✅ Датасет готов:")
    logger.success(f"   Персон: {len(id_map)}")
    logger.success(f"   Эмбеддингов: {len(embeddings_matrix)}")
    logger.success(f"   Форма матрицы: {embeddings_matrix.shape}")
    logger.success(f"   Сохранено в: {output_path}")


def build_faiss_index(embeddings_path: str, output_path: str):
    """Построение FAISS индекса из сохранённых эмбеддингов."""
    try:
        import faiss
    except ImportError:
        logger.error("Установите faiss: pip install faiss-cpu")
        sys.exit(1)

    embeddings = np.load(embeddings_path)
    dim = embeddings.shape[1]

    logger.info(f"Построение FAISS IndexFlatIP (dim={dim}, n={len(embeddings)})...")

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings.astype(np.float32))

    faiss.write_index(index, output_path)
    logger.success(f"✅ FAISS индекс сохранён: {output_path} ({index.ntotal} векторов)")


def evaluate_recognition(embeddings_path: str, labels_path: str, threshold: float = 0.6):
    """
    Оценка точности распознавания методом Leave-One-Out.
    Для каждого вектора делаем поиск по остальным и считаем accuracy.
    """
    try:
        import faiss
    except ImportError:
        logger.error("pip install faiss-cpu")
        sys.exit(1)

    embeddings = np.load(embeddings_path).astype(np.float32)
    labels = np.load(labels_path)

    n = len(embeddings)
    correct = 0
    total_known = 0

    logger.info(f"Leave-One-Out оценка ({n} образцов, порог={threshold})...")

    for i in range(n):
        # Временный индекс без i-го элемента
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        sub_embs = embeddings[mask]
        sub_labels = labels[mask]

        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(sub_embs)

        query = embeddings[i:i+1]
        D, I = index.search(query, k=1)

        score = float(D[0][0])
        pred_label = sub_labels[int(I[0][0])] if score >= threshold else -1
        true_label = labels[i]

        total_known += 1
        if pred_label == true_label:
            correct += 1

    accuracy = correct / total_known * 100
    logger.success(f"\n📊 Результаты оценки:")
    logger.success(f"   Точность: {accuracy:.2f}% ({correct}/{total_known})")
    logger.success(f"   Порог: {threshold}")
    return accuracy


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AttendAI ML Tools")
    subparsers = parser.add_subparsers(dest="command")

    # prepare
    prepare_parser = subparsers.add_parser("prepare", help="Подготовить датасет")
    prepare_parser.add_argument("--photos-dir", required=True)
    prepare_parser.add_argument("--output-dir", default="./dataset")

    # index
    index_parser = subparsers.add_parser("build-index", help="Построить FAISS индекс")
    index_parser.add_argument("--embeddings", required=True)
    index_parser.add_argument("--output", default="./faiss.index")

    # eval
    eval_parser = subparsers.add_parser("evaluate", help="Оценить точность")
    eval_parser.add_argument("--embeddings", required=True)
    eval_parser.add_argument("--labels", required=True)
    eval_parser.add_argument("--threshold", type=float, default=0.6)

    args = parser.parse_args()

    if args.command == "prepare":
        prepare_dataset(args.photos_dir, args.output_dir)
    elif args.command == "build-index":
        build_faiss_index(args.embeddings, args.output)
    elif args.command == "evaluate":
        evaluate_recognition(args.embeddings, args.labels, args.threshold)
    else:
        parser.print_help()

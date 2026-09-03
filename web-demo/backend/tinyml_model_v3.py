# tinyml_model_v3.py
# iTantra M3 -- V3 TinyML Character-Level 1D CNN Semantic Role Classifier
# V2 artifacts are NEVER modified. All V3 outputs use _v3_ prefix.

import os, json
import numpy as np
from typing import List, Dict, Tuple, Optional
import tensorflow as tf
from tinyml_dataset import ROLES, ROLE2ID, ID2ROLE

_BACKEND_DIR     = os.path.dirname(os.path.abspath(__file__))
MODEL_V3_KERAS   = os.path.join(_BACKEND_DIR, "tinyml_model_v3_fp32.keras")
MODEL_V3_FP32_TF = os.path.join(_BACKEND_DIR, "tinyml_model_v3_fp32.tflite")
MODEL_V3_INT8_TF = os.path.join(_BACKEND_DIR, "tinyml_model_v3_int8.tflite")
TOKENIZER_V3     = os.path.join(_BACKEND_DIR, "tinyml_v3_tokenizer.json")

MAX_LEN     = 128
EMBED_DIM   = 32
FILTERS_1   = 64
KERNEL_1    = 3
FILTERS_2   = 64
KERNEL_2    = 5
DENSE_DIM   = 64
DROPOUT     = 0.2
NUM_CLASSES = len(ROLES)  # 10


class CharTokenizer:
    """Minimal character-level tokenizer. Handles multilingual Unicode.
    Special tokens: 0=PAD, 1=UNK.
    """
    PAD_IDX = 0
    UNK_IDX = 1
    RESERVED = 2

    def __init__(self):
        self.char2idx = {}
        self.idx2char = {}
        self.vocab_size = 0

    def build_vocab(self, texts, max_vocab=512):
        from collections import Counter
        freq = Counter()
        for t in texts:
            freq.update(t)
        sorted_chars = [ch for ch, _ in sorted(freq.items(), key=lambda x: (-x[1], ord(x[0])))]
        sorted_chars = sorted_chars[:max_vocab - self.RESERVED]
        self.char2idx = {ch: i + self.RESERVED for i, ch in enumerate(sorted_chars)}
        self.idx2char = {v: k for k, v in self.char2idx.items()}
        self.idx2char[self.PAD_IDX] = '<PAD>'
        self.idx2char[self.UNK_IDX] = '<UNK>'
        self.vocab_size = len(sorted_chars) + self.RESERVED
        print(f"[V3 Tokenizer] Vocabulary size: {self.vocab_size} characters")

    def encode(self, text, max_len=MAX_LEN):
        ids = [self.char2idx.get(ch, self.UNK_IDX) for ch in text[:max_len]]
        ids.extend([self.PAD_IDX] * (max_len - len(ids)))
        return ids

    def encode_batch(self, texts, max_len=MAX_LEN):
        return np.array([self.encode(t, max_len) for t in texts], dtype=np.int32)

    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({"char2idx": self.char2idx, "vocab_size": self.vocab_size, "max_len": MAX_LEN},
                      f, ensure_ascii=False, indent=2)
        print(f"[V3 Tokenizer] Saved: {path}")

    @classmethod
    def load(cls, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        tok = cls()
        tok.char2idx = data["char2idx"]
        tok.idx2char = {v: k for k, v in tok.char2idx.items()}
        tok.idx2char[cls.PAD_IDX] = '<PAD>'
        tok.idx2char[cls.UNK_IDX] = '<UNK>'
        tok.vocab_size = data["vocab_size"]
        return tok


def format_context_string(span, left_ctx='', right_ctx=''):
    return f"[L] {left_ctx.strip()} [S] {span.strip()} [R] {right_ctx.strip()}"


def samples_to_texts(samples):
    return [format_context_string(s.get('span',''), s.get('left_ctx',''), s.get('right_ctx',''))
            for s in samples]


def build_model(vocab_size):
    """V3 char-level 1D CNN. Input: (MAX_LEN,) int32. Output: (NUM_CLASSES,) softmax."""
    inputs = tf.keras.Input(shape=(MAX_LEN,), dtype=tf.int32, name='char_input')
    x = tf.keras.layers.Embedding(input_dim=vocab_size, output_dim=EMBED_DIM,
                                   name='char_embedding')(inputs)
    x = tf.keras.layers.Conv1D(FILTERS_1, KERNEL_1, padding='same',
                                activation='relu', name='conv1d_k3')(x)
    x = tf.keras.layers.MaxPool1D(pool_size=2, name='maxpool_1')(x)
    x = tf.keras.layers.Conv1D(FILTERS_2, KERNEL_2, padding='same',
                                activation='relu', name='conv1d_k5')(x)
    x = tf.keras.layers.GlobalMaxPool1D(name='global_maxpool')(x)
    x = tf.keras.layers.Dense(DENSE_DIM, activation='relu', name='dense_hidden')(x)
    x = tf.keras.layers.Dropout(DROPOUT, name='dropout')(x)
    outputs = tf.keras.layers.Dense(NUM_CLASSES, activation='softmax', name='output_probs')(x)
    return tf.keras.Model(inputs=inputs, outputs=outputs, name='tinyml_v3_char_cnn')


def train_v3(train_samples, tokenizer=None, epochs=40, batch_size=64,
             validation_split=0.1, verbose=1):
    """Train V3. Returns (model, tokenizer, history)."""
    texts  = samples_to_texts(train_samples)
    labels = np.array([s['role_id'] for s in train_samples], dtype=np.int32)
    if tokenizer is None:
        tokenizer = CharTokenizer()
        tokenizer.build_vocab(texts, max_vocab=512)
    X = tokenizer.encode_batch(texts)
    model = build_model(vocab_size=tokenizer.vocab_size)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=3e-3),
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy'],
    )
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5,
                                         restore_best_weights=True, verbose=1),
        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                                             patience=3, min_lr=1e-5, verbose=1),
    ]
    history = model.fit(X, labels, epochs=epochs, batch_size=batch_size,
                        validation_split=validation_split, callbacks=callbacks,
                        verbose=verbose)
    return model, tokenizer, history


def save_keras(model, path=MODEL_V3_KERAS):
    model.save(path)
    print(f"[V3] Keras model saved: {path} ({os.path.getsize(path)/1024:.1f} KB)")


def load_keras(path=MODEL_V3_KERAS):
    return tf.keras.models.load_model(path)


def export_fp32_tflite(model, path=MODEL_V3_FP32_TF):
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()
    with open(path, 'wb') as f:
        f.write(tflite_model)
    print(f"[V3] FP32 TFLite saved: {path} ({os.path.getsize(path)/1024:.1f} KB)")
    return tflite_model


def export_int8_tflite(model, calib_X, path=MODEL_V3_INT8_TF):
    """PTQ INT8. calib_X: shape (N, MAX_LEN) int32 representative dataset."""
    def representative_dataset_gen():
        for i in range(len(calib_X)):
            yield [calib_X[i:i+1].astype(np.int32)]
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    converter.representative_dataset = representative_dataset_gen
    tflite_model = converter.convert()
    with open(path, 'wb') as f:
        f.write(tflite_model)
    print(f"[V3] INT8 TFLite saved: {path} ({os.path.getsize(path)/1024:.1f} KB)")
    return tflite_model


class TFLiteInferenceEngine:
    """TFLite interpreter wrapper. Handles FP32 and INT8 models."""
    def __init__(self, model_path):
        self.model_path  = model_path
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        self.input_details  = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.input_dtype    = self.input_details[0]['dtype']
        self.output_dtype   = self.output_details[0]['dtype']
        self.input_index    = self.input_details[0]['index']
        self.output_index   = self.output_details[0]['index']
        self.output_quant   = self.output_details[0].get('quantization', (1.0, 0))
        self.input_quant    = self.input_details[0].get('quantization', (1.0, 0))

    def predict_proba_single(self, x):
        if self.input_dtype == np.int8:
            scale, zp = self.input_quant
            if scale > 0:
                inp = np.round(x.astype(np.float32) / scale + zp).clip(-128, 127).astype(np.int8)
            else:
                inp = x.astype(np.int8)
            inp = inp.reshape(1, -1)
        else:
            inp = x.reshape(1, -1).astype(self.input_dtype)
        self.interpreter.set_tensor(self.input_index, inp)
        self.interpreter.invoke()
        out = self.interpreter.get_tensor(self.output_index)[0]
        if self.output_dtype == np.int8:
            scale, zp = self.output_quant
            out = (out.astype(np.float32) - zp) * scale
            out = np.clip(out, 0.0, None)
            s = out.sum()
            if s > 0: out = out / s
        return out.astype(np.float32)

    def predict_batch(self, X):
        results = np.zeros((len(X), NUM_CLASSES), dtype=np.float32)
        for i in range(len(X)):
            results[i] = self.predict_proba_single(X[i])
        return results

    def print_tensor_details(self):
        in_dt  = getattr(self.input_dtype,  '__name__', str(self.input_dtype))
        out_dt = getattr(self.output_dtype, '__name__', str(self.output_dtype))
        print(f"  Input  : shape={self.input_details[0]['shape']}, dtype={in_dt}")
        print(f"  Output : shape={self.output_details[0]['shape']}, dtype={out_dt}")
        if self.output_dtype == np.int8:
            s, zp = self.output_quant
            print(f"  Output quant: scale={s:.6f}, zero_point={zp}")
        if self.input_dtype == np.int8:
            s, zp = self.input_quant
            print(f"  Input  quant: scale={s:.6f}, zero_point={zp}")

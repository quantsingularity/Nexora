def build_deep_fm(hidden_units, embedding_dims, num_features):
    inputs = {
        f"feature_{i}": tf.keras.Input(shape=(1,), name=f"feature_{i}")
        for i in range(num_features)
    }

    # Factorization Machine Component
    embeddings = [
        layers.Embedding(input_dim=1e5, output_dim=embedding_dims)(inp)
        for inp in inputs.values()
    ]
    fm_term = 0.5 * tf.reduce_sum(
        tf.square(tf.reduce_sum(embeddings, axis=0))
        - tf.reduce_sum(tf.square(embeddings), axis=0)
    )

    # Deep Component
    deep = layers.concatenate(embeddings)
    for units in hidden_units:
        deep = layers.Dense(units, activation="selu")(deep)

    # Combine FM + Deep
    output = layers.Dense(1, activation="sigmoid")(layers.concatenate([fm_term, deep]))

    return tf.keras.Model(inputs=inputs, outputs=output)

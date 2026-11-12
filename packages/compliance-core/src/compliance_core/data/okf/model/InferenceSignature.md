---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: Compliance Model Type
title: InferenceSignature
description: Input/output signature of a model's inference function, specifying tensor types, shapes, and optional inference-time parameters.
tags: [model, inference, signature, tensor, schema]
schema: ../okb/schemas/InferenceSignature.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

`InferenceSignature` is embedded in a Model entity. It specifies the input and
output tensors for traceability and fairness auditing: knowing the exact input
features a model accepts is a prerequisite for identifying proxy attributes (see
[AttributeRef](/context/AttributeRef.md)).

# Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `inputs` | list of TensorSpec | no | Input tensor descriptors. |
| `outputs` | list of TensorSpec | no | Output tensor descriptors. |
| `parameters` | list of ParameterSpec | no | Optional inference-time parameters (e.g. `temperature`, `top_k`). |

## TensorSpec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Tensor name. |
| `dtype` | NumericType | yes | `FP16` · `FP32` · `FP64` · `INT8` · `INT16` · `INT32` · `INT64` · `UINT8` · `UINT16` · `UINT32` · `UINT64` · `BOOL` · `BYTES` |
| `shape` | list of int | no | Shape dimensions; `-1` denotes a variable-length dimension. |
| `description` | string | no | Semantic description of the tensor. |

## ParameterSpec

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Parameter name. |
| `dtype` | DataType | yes | `INT` · `FLOAT` · `STRING` · `BOOL` · `STRUCT` · `ARRAY` · `MAP` · `BYTES` · `DATE` · `DATETIME` · `CUSTOM` |
| `default_value` | any | no | Default value. |
| `description` | string | no | Description. |

# Examples

```json
{
  "inputs": [
    { "name": "input_ids",       "dtype": "INT64",  "shape": [-1, 512] },
    { "name": "attention_mask",  "dtype": "INT64",  "shape": [-1, 512] }
  ],
  "outputs": [
    { "name": "logits", "dtype": "FP32", "shape": [-1, 2] }
  ],
  "parameters": [
    { "name": "temperature", "dtype": "FLOAT", "default_value": 1.0 }
  ]
}
```

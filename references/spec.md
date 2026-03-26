# Spec Contract

The bridge expects JSON with this shape:

```json
{
  "version": "v1",
  "model": {
    "name": "PIDDemo",
    "description": "PID controller driving a transfer function plant",
    "sourcePrompt": "optional natural language source"
  },
  "blocks": [
    {
      "id": "Reference",
      "type": "Inport",
      "libraryPath": "simulink/Sources/In1",
      "params": {},
      "position": [40, 130, 70, 150]
    }
  ],
  "connections": [
    {
      "srcBlock": "Reference",
      "srcPort": 1,
      "dstBlock": "Plant",
      "dstPort": 1
    }
  ],
  "simulation": {
    "stopTime": "10",
    "solver": "ode45",
    "stepSize": ""
  },
  "validation": {
    "compileCheck": true,
    "smokeTest": true,
    "expectedSignals": []
  },
  "issues": []
}
```

Required top-level fields:

- `model`
- `blocks`
- `connections`
- `simulation`
- `validation`

The agent should prefer supported block `type` values and can omit `libraryPath` when the default entry from `catalog` is acceptable.

# Runtime Messaging Specification

The runtime server is used to mutate and retrieve the robot's state.
Requests and responses to the server are transported over TCP sockets, and the contents of these bytestreams are JSON serialized using [`msgpack`](https://msgpack.org/).

## Runtime Server Request

All fields optional:

```
{
  "timestamp": <unix_epoch: int>,
  "team": "(blue|gold|clear)",
  "starting_zone": "(left|right|prod_shelf|vending|clear)",
  "mode": "(idle|auto|teleop|estop)",
  "sensor_map": {
    "<sensor_uid: str>": "<name: str>",
    ...
  },
  "codegen_seed": <seed: int>,
  "window_interval": <seconds: float>,
  "msg_sent": <int>,
  "msg_recv": <int>
}
```

`window_interval` is used for configuring the length of the flow control interval.
That is, the `msg_sent` and `msg_recv` counts are reset every `window_interval` seconds.

## Runtime Server Response

All fields will be included.

```
{
  "timestamp": <unix_epoch: int>,
  "sensor_types": {
    "<sensor_name>": {
      "<parameter_name>": "(float|int|bool|str)",
    },
    ...
  },
  "sensor_map": {
    "<sensor_uid: str>": "<name: str>",
    ...
  },
  "msg_sent": <int>,
  "msg_recv": <int>,
  "student_code_hash": "<str>"
}
```

Robot Plumbing
==============

This guide covers some architectural aspects of the robot Runtime and its
subcomponents. It may be useful in the future when circumstances change
to understand why certain design decisions were made.

Overall Architecture
--------------------

Runtime is composed of a set of processes that talk to each other using
pipes and queues. The main Runtime process spawns and keeps track of
a few subprocesses:

- The UDP send process sends device data to Dawn
- The UDP receive process receives controller data from Dawn
- The TCP process sends console data to and receives essential messages from
  Dawn
- The student code process runs student code in isolation
- State Manager stores many parts of Runtime's state
- Hibike talks to devices using and forwards the results to State Manager

These parts of the system are run as separate processes to isolate them from
each other; each part can be stopped and started by Runtime independently.

<aside>
Even though State Manager can technically be stopped, if it dies, the whole
system will crash, so this is not strictly true.
</aside>

In exchange for this isolation, communication between processes is relatively
slow, and in the past, it has been a significant bottleneck between Hibike
and State Manager.

Runtime
-------

Runtime acts as the supervisor of all subprocesses, and keeps track of the
competition phase that the robot is in, along with the connections to
Dawn.

Ansible
-------

Ansible consists of three processes: the UDP send and receive processes, and the
TCP process. It connects to and communicates with Dawn over WiFi.

### UDP Send and Receive ###

[UDP](https://en.wikipedia.org/wiki/User_Datagram_Protocol) is a protocol
that provides unreliable, low-latency communication. In Ansible, we use it to
send sensor data and receive gamepad data because we want the robot to react quickly
to button presses and joystick moves. This data is sent multiple times per second,
so as long as the network is not too unreliable, it is OK if a few pieces
don't arrive.

### TCP ###
[TCP](https://en.wikipedia.org/wiki/Transmission_Control_Protocol) is a protocol
that provides reliable communication. In Ansible, we use it to send console
messages to Dawn and receive essential inputs, like emergency stop messages.
TCP adds latency to a connection in exchange for reliability, so it is only
useful for messages that can tolerate this tradeoff.

### Protobufs ###
Dawn is written in a different programming language (Javascript) than Runtime.
We must talk to it in a way that can be understood by both sides. For this
purpose, we use Protocol Buffers, a Google library.

State Manager
-------------
todo

Student Code
------------
todo

Hibike
------

### Concurrency ###

### The Hibike Protocol ###

### Smart Devices ###



# Clustered Unity (Distributed Clustering)

Makes multiple hardware instances pool memory/CPU and behave as a single distributed Janet entity using RAFT-like consensus.

## Overview

The cluster orchestrator enables multiple Janet Mesh server instances to work together as a unified distributed system, sharing resources and maintaining a single identity.

## Architecture

```
Node 1 (Leader) ←→ Node 2 (Follower) ←→ Node 3 (Follower)
     ↓                   ↓                    ↓
    Shared Memory Pool (Redis or In-Memory)
```

## Key Components

### Cluster Orchestrator (`server/cluster/cluster_orchestrator.py`)

- RAFT-like leader election protocol
- Node discovery via Bonjour/mDNS (extends existing discovery)
- Health checks and automatic failover
- Inter-process communication via ZeroMQ

### Shared Memory Pool (`server/cluster/shared_memory.py`)

- Cluster-wide short-term memory cache
- Conversation context sharing
- Task queue distribution
- Uses local Redis instance (offline-first) or in-memory fallback

### Identity Manager (`server/cluster/identity_manager.py`)

- Shared identity key across cluster
- Prime instance selection (leader becomes "voice of Janet")
- Load balancing for LLM requests
- CPU/memory resource pooling

## RAFT Consensus

### Node States

- **Follower**: Default state, receives heartbeats from leader
- **Candidate**: Seeking votes during election
- **Leader**: Processes requests and sends heartbeats
- **Disconnected**: Node health check failed

### Leader Election

1. Follower detects leader is unhealthy (no heartbeat)
2. Increments term and becomes Candidate
3. Votes for self and requests votes from other nodes
4. If majority votes received → becomes Leader
5. Announces leadership to cluster

### Heartbeat Mechanism

- Leader sends heartbeat every `heartbeat_interval` (default: 5s)
- Followers update last_heartbeat timestamp
- If `election_timeout` (default: 15s) passes without heartbeat → trigger election

## Shared Memory

### Redis Configuration

```python
SharedMemoryPool(
    host="localhost",
    port=6379,
    db=0,
    password=None,  # Optional
    use_redis=True  # Falls back to in-memory if False
)
```

### In-Memory Fallback

If Redis is unavailable, the system uses an in-memory dictionary with expiration times. This ensures clustering works offline-first.

## Identity Management

### Prime Instance

The **Prime Instance** is the current leader, designated as the "voice of Janet". Only the prime instance should process LLM requests to maintain consistency.

### Identity Key

A shared identity key is stored in shared memory, allowing all nodes to verify they belong to the same cluster.

### Load Balancing

Requests are distributed to the least loaded node:
- Tracks request count per node
- Considers CPU and memory usage
- Selects node with lowest combined load

## Integration

### WebSocket Server

The cluster orchestrator is initialized in `websocket_server.py`:

```python
self.cluster_orchestrator = ClusterOrchestrator()
self.shared_memory = SharedMemoryPool(use_redis=False)
self.identity_manager = IdentityManager(
    cluster_orchestrator=self.cluster_orchestrator,
    shared_memory=self.shared_memory
)
```

### Janet Adapter

Janet adapter checks cluster mode before processing:

```python
if self.cluster_mode and self.identity_manager:
    if not self.identity_manager.is_prime_instance():
        # Route to prime instance or process anyway with warning
        logger.warning("Request on non-prime instance")
```

### Cluster Status Endpoint

Clients can query cluster status:

```json
{
  "type": "cluster_status"
}
```

Response:
```json
{
  "type": "cluster_status",
  "available": true,
  "cluster": {
    "node_id": "uuid",
    "state": "leader",
    "current_term": 5,
    "leader_id": "uuid",
    "is_leader": true,
    "node_count": 3
  },
  "identity": {
    "prime_instance_id": "uuid",
    "is_prime": true
  }
}
```

## Node Discovery

### Bonjour/mDNS

Nodes discover each other via Bonjour service discovery:
- Service type: `_janet-mesh._tcp`
- Port: 8765 (WebSocket) + 8766 (Cluster communication)
- Automatic discovery on local network

### Manual Node Addition

Nodes can be added manually:
```python
orchestrator.add_node(
    node_id="manual-node-id",
    address="192.168.1.100",
    port=8766,
    state=NodeState.FOLLOWER
)
```

## Resource Pooling

### CPU Pooling

Nodes report CPU usage:
```python
identity_manager.update_resource_usage(
    node_id="uuid",
    cpu_percent=45.2,
    memory_percent=62.8
)
```

### Memory Pooling

Shared memory pool provides:
- Cluster-wide context cache
- Conversation history sharing
- Task queue distribution

## Health Checks

### Automatic Health Monitoring

- Checks heartbeat timestamps every 2 seconds
- Marks nodes as unhealthy if heartbeat stale
- Triggers election if leader is unhealthy

### Manual Health Check

```python
status = orchestrator.get_cluster_status()
# Returns detailed cluster state
```

## Failover

### Automatic Failover

1. Leader becomes unhealthy (no heartbeat for 15s)
2. Followers detect leader failure
3. Election triggered automatically
4. New leader elected via RAFT consensus
5. Cluster continues operation

### Zero Downtime

- Requests continue during election (buffered or queued)
- New leader picks up processing immediately
- Shared memory ensures context is preserved

## Configuration

### Cluster Port

Default: `8766` (separate from WebSocket port 8765)

### Heartbeat Interval

Default: `5.0` seconds

### Election Timeout

Default: `15.0` seconds

## Limitations

- Requires local network (for node discovery)
- ZeroMQ required for inter-node communication
- Redis optional (falls back to in-memory)
- Single leader processes all requests (no horizontal scaling yet)

## Future Enhancements

- Horizontal scaling with request routing
- Distributed LLM inference
- Cross-network clustering (VPN)
- Cluster metrics and monitoring dashboard

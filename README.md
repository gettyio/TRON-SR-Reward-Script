# TRON-SR-Reward-Script
Python scripts for SR rewards


Requires base58 lib from pip

```

sudo pip install base58

```

Connects to a local node, can be configured for a remote node but it uses unsafe remote node signing.

Configure these at the top of the script:
```

SELF_ADDRESS = ""
PK = ""
DIST_PERCENT = 90.0
```

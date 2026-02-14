#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
docker compose exec -T backend python3 tests/verify_ranged_combat.py

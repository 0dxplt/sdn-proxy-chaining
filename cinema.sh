#!/bin/bash
SESSION="proxy_chains"
tmux new-session -d -s $SESSION
tmux split-window -v -t $SESSION:0.0
tmux split-window -h -t $SESSION:0.0
tmux split-window -h -t $SESSION:0.2
tmux select-layout tiled
tmux send-keys -t $SESSION:0.0 'sudo -E python3 main.py tmux' C-m
tmux select-pane -t $SESSION:0.0
tmux attach -t $SESSION
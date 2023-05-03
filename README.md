# Herodotus K8s Scheduler

TODO: fill this out ;)

## Steps:
- Plan out how scheduling lifecycle works function-by-function
- Look at how each plugin-calling function in Framework runtime works, see what kind of data needs to be added
- Plan out what data to store in CycleState from the framework runtime
- Using metrics as way to display data:
    - Normalized Score by Node
    - Normalized Score Total by Node
    - Normalized Score by plugin by node
    - Filter status by by pod by plugin by node 


## Reminders:
- Make scheduler package public on Github

## Edge Cases:
- Choosing a node when only one option is available
- Choosing a nominated node from preemption

## K8s Source Files Modified:
- kubernetes_src/pkg/scheduler/framework/types.go
- kubernetes_src/pkg/scheduler/metrics/metrics.go
- kubernetes_src/pkg/scheduler/schedule_one.go
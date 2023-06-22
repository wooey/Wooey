broker_url = "amqp://guest@rabbit:5672"
track_started = True
send_events = True
imports = ("wooey.tasks",)
task_serializer = "json"
task_acks_late = True

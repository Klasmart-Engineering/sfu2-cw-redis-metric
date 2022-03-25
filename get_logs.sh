aws logs  start-query \
    --log-group-name "/aws/ecs/containerinsights/kl-research/performance" \
    --start-time $(date --date "-30 min" "+%s")  \
    --end-time $(date "+%s") \
    --query-string 'fields @timestamp, @log, @logStream, @message | filter ispresent(TaskId) and TaskId like /10a2278ca8674084a153e1146bf971e3|384f78c94bb848e0b27ce731aaa9ce76|410964cf453b440fa2ec18b56294d952|445136e48b15476c9d1cfc9ba07588ba|5d1298c3d5144781b27db628c7f84b61|dc2c9d29babf4470817e3c9010740413/ and Type = "Task" | sort @timestamp desc' \
    --profile kl-research-global

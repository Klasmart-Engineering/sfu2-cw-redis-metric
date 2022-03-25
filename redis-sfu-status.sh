#!/bin/bash

declare -A sfu_list


redis_host="src/redis-cli -h kl-research-live-redis-cluster.7aivwh.clustercfg.apn2.cache.amazonaws.com -c -p 6379"

echo "timestamp,instance,producers,consumers" > redis_sfu_stats-$(date +'%Y%m%d').csv

while true; do
        sleep 60
        sfu_list=$(${redis_host} keys 'sfu:*:status' | cut -f 2)

        for sfu in ${sfu_list[@]}
                do
                        sfu_status=$(${redis_host} mget ${sfu})
                        sfu_instance=$( echo $sfu_status | cut -d ":" -f 2 | cut -d "\"" -f 2)
                        sfu_producers=$( echo $sfu_status | cut -d ":" -f 4 | cut -d "," -f 1 )
                        sfu_consumers=$( echo $sfu_status | cut -d ":" -f 5 | cut -d "," -f 1 )
                        sfu_timestamp=$( echo $sfu_status | cut -d ":" -f 6 | cut -d "}" -f 1 )

                        echo "$sfu_timestamp,$sfu_instance,$sfu_producers,$sfu_consumers" >> redis_sfu_stats-$(date +'%Y%m%d').csv

                done
done


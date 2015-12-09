osascript 2>/dev/null <<EOF
    tell application "System Events"
        tell process "Terminal" to keystroke "t" using command down
    end
    tell application "Terminal"
        activate
        do script with command "postgres -D /usr/local/var/postgres" in window 0
    end
EOF
sleep 2
osascript 2>/dev/null <<EOF
    tell application "System Events"
        tell process "Terminal" to keystroke "t" using command down
    end
    tell application "Terminal"
        activate
        do script with command "cd \"$PWD/client\"; $*" in window 0
        do script with command "./clean_dev_build.sh" in window 0
    end
    tell application "System Events"
        tell process "Terminal" to keystroke "t" using command down
    end
    tell application "Terminal"
        activate
        do script with command "cd \"$PWD/server\"; $*" in window 0
        do script with command "./run.sh" in window 0
    end
EOF

#!/usr/bin/env bash
set -euo pipefail

readonly READY_PATTERN='Done \([0-9.]+s\)!|For help, type "help"'
readonly COMMAND_TIMEOUT_SECONDS=120
readonly SAVE_TIMEOUT_SECONDS=240
readonly STARTUP_TIMEOUT_SECONDS=360
readonly RCON_CLIENT='.github/scripts/minecraft_rcon.py'
readonly RCON_PASSWORD='cubicchunks-phase1'
readonly RCON_PORT=25575

server_pid=""

cleanup_server() {
    if [[ -n "${server_pid}" ]] && kill -0 "${server_pid}" >/dev/null 2>&1; then
        kill -INT -- "-${server_pid}" >/dev/null 2>&1 || true
        sleep 5
        kill -TERM -- "-${server_pid}" >/dev/null 2>&1 || true
        wait "${server_pid}" >/dev/null 2>&1 || true
    fi
    server_pid=""
}
trap cleanup_server EXIT

wait_for_log() {
    local log_file="$1"
    local pattern="$2"
    local timeout_seconds="$3"

    for _ in $(seq 1 "${timeout_seconds}"); do
        if grep -Eq "${pattern}" "${log_file}"; then
            return 0
        fi
        if [[ -n "${server_pid}" ]] && ! kill -0 "${server_pid}" >/dev/null 2>&1; then
            echo "Server exited while waiting for log pattern: ${pattern}" >&2
            cat "${log_file}" >&2
            return 1
        fi
        sleep 1
    done

    echo "Timed out waiting for log pattern: ${pattern}" >&2
    cat "${log_file}" >&2
    return 1
}

rcon_command() {
    local command="$1"
    shift
    python3 "${RCON_CLIENT}" \
        --host 127.0.0.1 \
        --port "${RCON_PORT}" \
        --password "${RCON_PASSWORD}" \
        "$@" \
        "${command}"
}

start_server() {
    local log_file="$1"

    : > "${log_file}"
    setsid ./gradlew runServer --stacktrace --no-daemon </dev/null >"${log_file}" 2>&1 &
    server_pid=$!

    wait_for_log "${log_file}" "${READY_PATTERN}" "${STARTUP_TIMEOUT_SECONDS}"
    rcon_command "list" --connect-timeout 60
}

stop_server() {
    local log_file="$1"

    rcon_command "stop" --allow-disconnect --timeout "${SAVE_TIMEOUT_SECONDS}" --connect-timeout 5 || true
    for _ in $(seq 1 "${COMMAND_TIMEOUT_SECONDS}"); do
        if ! kill -0 "${server_pid}" >/dev/null 2>&1; then
            wait "${server_pid}" || true
            server_pid=""
            return 0
        fi
        sleep 1
    done

    echo "Server did not stop cleanly." >&2
    cat "${log_file}" >&2
    return 1
}

mkdir -p run
printf 'eula=true\n' > run/eula.txt
cat > run/server.properties <<PROPERTIES
online-mode=false
view-distance=2
simulation-distance=2
max-tick-time=-1
level-name=phase1-persistence-world
motd=CubicChunks3 Persistence Smoke Test
enable-rcon=true
broadcast-rcon-to-ops=false
rcon.password=${RCON_PASSWORD}
rcon.port=${RCON_PORT}
PROPERTIES

first_log="server-persistence-first.log"
second_log="server-persistence-second.log"

start_server "${first_log}"
rcon_command "setblock 0 10 0 minecraft:diamond_block"
rcon_command "execute if block 0 10 0 minecraft:diamond_block run say CC_BLOCK_PLACED"
wait_for_log "${first_log}" "CC_BLOCK_PLACED" "${COMMAND_TIMEOUT_SECONDS}"
rcon_command "save-all flush" --timeout "${SAVE_TIMEOUT_SECONDS}" --connect-timeout 5
rcon_command "say CC_SAVE_FLUSH_FINISHED"
wait_for_log "${first_log}" "CC_SAVE_FLUSH_FINISHED" "${COMMAND_TIMEOUT_SECONDS}"
stop_server "${first_log}"

start_server "${second_log}"
rcon_command "execute if block 0 10 0 minecraft:diamond_block run say CC_BLOCK_RELOADED"
wait_for_log "${second_log}" "CC_BLOCK_RELOADED" "${COMMAND_TIMEOUT_SECONDS}"
stop_server "${second_log}"

echo "Cubic world block survived a clean save and server restart."

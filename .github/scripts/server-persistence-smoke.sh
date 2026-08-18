#!/usr/bin/env bash
set -euo pipefail

readonly READY_PATTERN='Done \([0-9.]+s\)!|For help, type "help"'
readonly LOAD_PATTERN='Loaded persisted cube'
readonly COMMAND_TIMEOUT_SECONDS=120
readonly SAVE_TIMEOUT_SECONDS=240
readonly STARTUP_TIMEOUT_SECONDS=360
readonly RCON_CLIENT='.github/scripts/minecraft_rcon.py'
readonly RCON_PASSWORD='cubicchunks-phase1'
readonly RCON_PORT=25575
readonly WORLD_DIRECTORY='run/phase1-persistence-world'
readonly CUBE_DIRECTORY="${WORLD_DIRECTORY}/cubicchunks/cubes"
readonly WORKSPACE_ROOT="$(pwd -P)"

server_pid=""

workspace_java_pids() {
    local process_path
    local process_id
    local executable
    local command_line

    for process_path in /proc/[0-9]*; do
        process_id=${process_path##*/}
        executable=$(readlink "${process_path}/exe" 2>/dev/null || true)
        if [[ "${executable}" != */java ]]; then
            continue
        fi

        command_line=$(tr '\0' ' ' < "${process_path}/cmdline" 2>/dev/null || true)
        if [[ "${command_line}" == *"${WORKSPACE_ROOT}"* ]]; then
            printf '%s\n' "${process_id}"
        fi
    done
}

capture_save_flush_thread_dumps() {
    local process_id
    local command_line
    local java_pids

    java_pids=$(workspace_java_pids || true)
    : > save-flush-processes.txt
    while read -r process_id; do
        if [[ -z "${process_id}" ]]; then
            continue
        fi

        command_line=$(tr '\0' ' ' < "/proc/${process_id}/cmdline" 2>/dev/null || true)
        printf 'PID %s: %s\n' "${process_id}" "${command_line}" >> save-flush-processes.txt
        jcmd "${process_id}" Thread.print -l > "save-flush-thread-${process_id}.txt" 2>&1 || true
    done <<< "${java_pids}"
}

wait_for_world_lock_release() {
    local lock_file="${WORLD_DIRECTORY}/session.lock"

    python3 - "${lock_file}" <<'PY'
import fcntl
import pathlib
import sys
import time

lock_file = pathlib.Path(sys.argv[1])
for _ in range(60):
    if not lock_file.exists():
        sys.exit(0)
    try:
        with lock_file.open("a+b") as handle:
            fcntl.lockf(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.lockf(handle, fcntl.LOCK_UN)
        sys.exit(0)
    except BlockingIOError:
        time.sleep(1)

print(f"World lock remained held: {lock_file}", file=sys.stderr)
sys.exit(1)
PY
}

terminate_server() {
    local process_id
    local remaining_pids

    if [[ -n "${server_pid}" ]] && kill -0 "${server_pid}" >/dev/null 2>&1; then
        kill -TERM -- "-${server_pid}" >/dev/null 2>&1 || true
    fi

    for _ in $(seq 1 20); do
        remaining_pids=$(workspace_java_pids || true)
        if [[ -z "${remaining_pids}" ]]; then
            break
        fi

        while read -r process_id; do
            [[ -n "${process_id}" ]] && kill -TERM "${process_id}" >/dev/null 2>&1 || true
        done <<< "${remaining_pids}"
        sleep 1
    done

    remaining_pids=$(workspace_java_pids || true)
    while read -r process_id; do
        [[ -n "${process_id}" ]] && kill -KILL "${process_id}" >/dev/null 2>&1 || true
    done <<< "${remaining_pids}"

    if [[ -n "${server_pid}" ]]; then
        kill -KILL -- "-${server_pid}" >/dev/null 2>&1 || true
        wait "${server_pid}" >/dev/null 2>&1 || true
    fi
    server_pid=""
}

cleanup_server() {
    terminate_server || true
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

stop_server_cleanly() {
    local log_file="$1"
    local remaining_pids

    rcon_command "stop" --allow-disconnect --timeout "${COMMAND_TIMEOUT_SECONDS}" --connect-timeout 5 || true
    for _ in $(seq 1 "${COMMAND_TIMEOUT_SECONDS}"); do
        remaining_pids=$(workspace_java_pids || true)
        if [[ -z "${remaining_pids}" ]]; then
            if [[ -n "${server_pid}" ]]; then
                wait "${server_pid}" >/dev/null 2>&1 || true
            fi
            server_pid=""
            wait_for_world_lock_release
            return 0
        fi
        sleep 1
    done

    echo "Server did not stop cleanly after the RCON stop command." >&2
    cat "${log_file}" >&2
    return 1
}

assert_complete_cube_files_exist() {
    local cube_count
    local temporary_count

    cube_count=$(find "${CUBE_DIRECTORY}" -type f -name '*.ccube' -print 2>/dev/null | wc -l)
    temporary_count=$(find "${CUBE_DIRECTORY}" -type f -name '*.tmp' -print 2>/dev/null | wc -l)
    if (( cube_count == 0 )); then
        echo "No complete persisted cube files were written." >&2
        return 1
    fi
    if (( temporary_count != 0 )); then
        echo "Found ${temporary_count} incomplete cube staging files after flush." >&2
        return 1
    fi
    echo "Flush completed with ${cube_count} complete persisted cube files."
}

rm -rf "${WORLD_DIRECTORY}"
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
if ! rcon_command "save-all flush" --timeout "${SAVE_TIMEOUT_SECONDS}" --connect-timeout 5 >save-flush-rcon.log 2>&1; then
    capture_save_flush_thread_dumps
    echo "save-all flush did not return normally." >&2
    exit 1
fi
assert_complete_cube_files_exist
rcon_command "say CC_SAVE_FLUSH_FINISHED"
wait_for_log "${first_log}" "CC_SAVE_FLUSH_FINISHED" "${COMMAND_TIMEOUT_SECONDS}"
stop_server_cleanly "${first_log}"

start_server "${second_log}"
wait_for_log "${second_log}" "${LOAD_PATTERN}" "${COMMAND_TIMEOUT_SECONDS}"
stop_server_cleanly "${second_log}"

echo "Cubic save-all flush returned, both servers stopped cleanly, and persisted cubes loaded after restart."

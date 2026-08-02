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

server_pid=""

terminate_server() {
    if [[ -z "${server_pid}" ]] || ! kill -0 "${server_pid}" >/dev/null 2>&1; then
        server_pid=""
        return 0
    fi

    kill -TERM -- "-${server_pid}" >/dev/null 2>&1 || true
    for _ in $(seq 1 10); do
        if ! kill -0 "${server_pid}" >/dev/null 2>&1; then
            wait "${server_pid}" >/dev/null 2>&1 || true
            server_pid=""
            return 0
        fi
        sleep 1
    done

    kill -KILL -- "-${server_pid}" >/dev/null 2>&1 || true
    wait "${server_pid}" >/dev/null 2>&1 || true
    server_pid=""
}

cleanup_server() {
    terminate_server
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

cube_file_count() {
    if [[ ! -d "${CUBE_DIRECTORY}" ]]; then
        printf '0\n'
        return
    fi
    find "${CUBE_DIRECTORY}" -type f -name '*.ccube' -print | wc -l
}

cube_temp_file_count() {
    if [[ ! -d "${CUBE_DIRECTORY}" ]]; then
        printf '0\n'
        return
    fi
    find "${CUBE_DIRECTORY}" -type f -name '*.tmp' -print | wc -l
}

wait_for_stable_cube_files() {
    local previous_count=-1
    local stable_seconds=0
    local cube_count
    local temporary_count

    for _ in $(seq 1 "${SAVE_TIMEOUT_SECONDS}"); do
        cube_count=$(cube_file_count)
        temporary_count=$(cube_temp_file_count)

        if (( cube_count > 0 && temporary_count == 0 && cube_count == previous_count )); then
            stable_seconds=$((stable_seconds + 1))
            if (( stable_seconds >= 10 )); then
                echo "First server wrote a stable set of ${cube_count} persisted cube files."
                return 0
            fi
        else
            stable_seconds=0
        fi

        previous_count=${cube_count}
        sleep 1
    done

    echo "Cube files did not reach a stable atomic state." >&2
    return 1
}

remove_incomplete_cube_staging_files() {
    local removed_count
    local remaining_count
    local cube_count

    sync
    removed_count=$(cube_temp_file_count)
    if (( removed_count > 0 )); then
        find "${CUBE_DIRECTORY}" -type f -name '*.tmp' -delete
        echo "Removed ${removed_count} incomplete cube staging files after forced shutdown."
    fi

    sync
    remaining_count=$(cube_temp_file_count)
    if (( remaining_count != 0 )); then
        echo "Incomplete cube staging files remain after cleanup." >&2
        return 1
    fi

    cube_count=$(cube_file_count)
    if (( cube_count == 0 )); then
        echo "No complete persisted cube files remain after cleanup." >&2
        return 1
    fi
    echo "Restarting with ${cube_count} complete persisted cube files and no staging files."
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
rcon_command "save-all flush" --timeout "${SAVE_TIMEOUT_SECONDS}" --connect-timeout 5 >save-flush-rcon.log 2>&1 &
save_rcon_pid=$!
wait_for_stable_cube_files
kill "${save_rcon_pid}" >/dev/null 2>&1 || true
wait "${save_rcon_pid}" >/dev/null 2>&1 || true
terminate_server
remove_incomplete_cube_staging_files

start_server "${second_log}"
wait_for_log "${second_log}" "${LOAD_PATTERN}" "${COMMAND_TIMEOUT_SECONDS}"
terminate_server

echo "Cubic world files were written atomically and loaded during a server restart."

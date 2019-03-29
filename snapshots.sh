#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd )"
BACKUP_DIR="${DIR}/snapshots_backup"
SNAP_DIR="${DIR}/snapshots"

# create directory
if [ ! -d "${BACKUP_DIR}" ]; then
	if ! mkdir -p "${BACKUP_DIR}"
	then
		echo -e "\033[;31mmkdir ${BACKUP_DIR} failed!!!\033[0m"
		exit 1
	fi
fi

# delete  old snapshots
if [ -d "${SNAP_DIR}" ]; then
	for old_file in $(ls "${SNAP_DIR}")
	do
		if ! rm -fr "${SNAP_DIR}/${old_file}"
		then
			echo -e "\033[;31mrm -fr ${old_file} failed!!!\033[0m"
			exit 1
		fi
	done
else
	if ! mkdir -p "${SNAP_DIR}"
	then
		echo -e "\033[;31mmkdir ${SNAP_DIR} failed!!!\033[0m"
		exit 1
	fi
fi

# create snapshots
DATE="$(date +"%Y-%m-%d-%H-%M-%S")"
curl http://127.0.0.1:8888/v1/producer/create_snapshot
if [ $? -ne 0 ]; then
	echo -e "\033[;31merror: ${DATE} create snapshots failed!!!\033[0m"
	exit 1
fi

# tar snapshots
NAME="eospark_${DATE}.tar"
SNAP_FILE="$(ls ${SNAP_DIR})"
cd "${DIR}" && tar -czvf "${NAME}" "snapshots/${SNAP_FILE}" && mv "${NAME}" "${BACKUP_DIR}" && rm -fr "${SNAP_DIR}/${SNAP_FILE}" 
if [ $? -ne 0 ]; then 
	echo -e "\033[;31merror: ${DATE} tar snapshots ${NAME} failed!!!\033[0m"
	exit 1 
fi

echo -e "\033[;32m${DATE} tar snapshots ${NAME} succed\033[0m"



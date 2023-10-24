#!/bin/sh

OPEN_LAB=/home/bsijober/FirmwaresFOX/openlab/
OOCD_ITF=${OPEN_LAB}/platform/scripts/mysticjtag.cfg
OOCD_TARGET=stm32f1x
EXECUTABLE_OUTPUT_PATH=.
ARGV0=$1

if test $# -eq 1
then
openocd -f "${OOCD_ITF}" \
	-f "target/${OOCD_TARGET}.cfg" \
	-c "init" \
	-c "targets" \
	-c "reset halt" \
	-c "reset init" \
	-c "flash write_image erase ${EXECUTABLE_OUTPUT_PATH}/${ARGV0}" \
	-c "verify_image ${EXECUTABLE_OUTPUT_PATH}/${ARGV0}" \
	-c "reset run" \
	-c "shutdown" 
else
     echo "flash: file_to_flash.elf"
fi



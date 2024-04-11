C_NAME := new_publisher
C_CODE := src/pysv/c_package/$(C_NAME).c

.PHONY: build
build: $(C_CODE)
	cc -c $(C_CODE) -o $(C_NAME)

.PHONY: run
run:
	sudo PYSV_INTERFACE="enp0s31f6" nice -n -20 .venv/bin/python -m pysv -debug

.PHONY: clean
clean: $(C_NAME)
	rm $(C_NAME)

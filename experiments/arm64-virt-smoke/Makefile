CROSS ?= aarch64-linux-gnu-
CC := $(CROSS)gcc
BUILD := build

.PHONY: all clean
all: $(BUILD)/hello.elf

$(BUILD)/hello.elf: hello.S linker.ld
	mkdir -p $(BUILD)
	$(CC) -nostdlib -nostartfiles -static -Wl,--build-id=none -Wl,-T,linker.ld -o $@ hello.S

clean:
	$(RM) $(BUILD)/hello.elf

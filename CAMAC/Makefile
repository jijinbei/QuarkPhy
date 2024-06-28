# Makefile for scalar.c

# コンパイラの設定
CC = gcc
CFLAGS = -Wall -Wextra -O2

# プロジェクトの名前
TARGET = scalar
#gcc scaler.c -std=c99 -o scaler -I camdrv-1.1.0/camdrv/ camdrv-1.1.0/camdrv/toyocamac.o camdrv-1.1.0/camdrv/camlib.o
# ソースファイルとオブジェクトファイルのリスト
SRCS = scalar.c
OBJS = $(SRCS:.c=.o)

# ライブラリ
LIBRARY = camdrv.o toyocamac.o

# デフォルトのターゲット
all: $(TARGET)

# 実行ファイルをリンク
$(TARGET): $(OBJS) $(LIBRARY)
    $(CC) $(CFLAGS) -o $(TARGET) $(OBJS) $(LIBRARY)

# 各ソースファイルをコンパイル
%.o: %.c
    $(CC) $(CFLAGS) -c $< -o $@

# クリーンアップ
clean:
    rm -f $(OBJS) $(TARGET)

# フォースリビルド
.PHONY: all clean

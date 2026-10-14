/* The plugin ABI is one function taking/returning int. */
int ch07_transform(int value) {
    return value >= 0 && value <= 100 ? value + 7 : -1;
}

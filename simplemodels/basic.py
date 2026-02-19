def ThisIsFunction(x: int) -> float:
    if x % 2 == 0:
        return x / 2


def another_function(y: int):
    return y * x


if __name__ == "__main__":
    x = int(input())
    res1 = ThisIsFunction(x)
    res2 = another_function(res1)

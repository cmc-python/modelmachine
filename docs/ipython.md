# IPython

Поддерживается интеграция в ipython/jupyter с помощью
[cell magic](https://ipython.org/ipython-doc/stable/interactive/reference.html#magic-command-system).

Сначала выполните импорт

```py
import modelmachine.ipython
```

Затем можете использовать cell magic:
- `%%mm.debug` - отладка
- `%%mm.run` - запуск
- `%%mm.asm` - ассемблирование

```py
%%mm.debug

.cpu mm-3

.input 0x6
.output 0x7

.code
00 0005 0000 0007 ; 0 move 1 R
03 0007 0006 0007 ; 1 smul R N =: R
02 0006 0005 0006 ; 2 sub N 1 =: N
86 0006 0005 0001 ; 3 N > 1 -> 0001
99 0000 0000 0000 ; 4 halt
00 0000 0000 0001 ; 5 =1
                  ; 6 N
                  ; 7 R
.enter 6
```

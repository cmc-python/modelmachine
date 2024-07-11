# modelmachine
Model machine emulator

## Модельная машина

Модельная машина - это чистая архитектурная концепция, позволяющая понять
логику функционирования центральных процессоров. По своей структуре она близка
к компьютерам первого поколения. Подробнее читайте по ссылкам внизу.

## Quickstart

Установка пакета происходит командой:

    # python3 -m pip install --upgrade modelmachine

После этого вам становится доступна консольная команда `modelmachine`.

Посмотрите примеры в папке [samples](samples/), по их образу можно начинать писать
программы для модельных машин. Запуск программы производится командой:

    $ modelmachine run samples/mm-3_sample.mmach

Также доступна пошаговая отладка командой:

    $ modelmachine debug samples/mm-3_sample.mmach

Поддерживается компилирование ассемблера модельной машины (mmasm) в ее машинный
код.

    $ modelmachine asm source.mmasm result.mmach

### [Пример](samples/mm-3_sample.mmach)

    .cpu mm-3

    .input 0x100 a
    .input 0x101 b
    .output 0x103 x

    .code
    ; x = ((a * -21) % 50 - b) ** 2 == 178929
    03 0100 0005 0103 ; x := a * -21
    04 0103 0006 0102 ; [0102] := x / 50, x := x % 50
    02 0103 0101 0103 ; x := x - b
    03 0103 0103 0103 ; x := x * x
    99 0000 0000 0000 ; halt
    ; ---------------------
    FFFFFFFFFFFFEB ; -21
    00000000000032 ; 50

    .enter -123 456

* Все, что идет после символа `;` - комментарий; пустые строки игнорируются.
* Программа должна начинаться с директивы `.cpu` и указания архитектуры.
  Список поддерживаемых архитектур смотри ниже.
* Текст программы обязан содержать директиву `.code` после которой идет
  секция кода, содержащая набор 16-ричных чисел, записываемых в
  память модельной машины. Пропускать часть машинного слова нельзя.
  Рекомендуется писать по одному машинному слову в строке, по желанию
  разбивая разряды на части пробелами.
* Директива `.input ADDRESS [QUESTION]` читает данные из потока ввода
  по адресу `ADDRESS` до запуска модельной машины.
  - `ADDRESS` может использовать десятичный `15` или шеснадцатеричный
    `0xff` формат.
  - Вводить также можно десятичные и шеснадцатеричные числа со знаком.
  - При вводе из консоли, пользователь увидит вопрос `QUESTION`; при
    вводе из файла `QUESTION` будет игнорироваться.
* Необязательная директива `.enter NUMBERS...` вводит числа в поток ввода
  вместо потока ввода.
  - Если запуск программы производится с ключом `-enter`, то директива
    `.enter` игнорируется.
  - Это позволяет для отладки записать данные вместе с программой, а потом
    запускать ее из консоли с разными параметрами.
* Директива `.output ADDRESS [MESSAGE]` печатает данные в поток вывода
  после завершения модельной машины.
  - Данные печатаются в виде десятичных чисел со знаком.
  - Если произошла ошибочная ситуация (например, деление на 0),
    то вывод производится не будет.
* Больше примеров в папке [samples](samples/)

## Таблица команд модельных машин

|OPCODE|mm-3 |mm-2 |mm-v |mm-1 |mm-r |mm-m  |
|:-----|:---:|:---:|:---:|:---:|:---:|:----:|
|0x00  |move |move |move |load |load | load |
|0x01  | add | add | add | add | add | add  |
|0x02  | sub | sub | sub | sub | sub | sub  |
|0x03  |smul |smul |smul |smul |smul | smul |
|0x04  |sdiv |sdiv |sdiv |sdiv |sdiv | sdiv |
|0x05  |     |comp |comp |comp |comp | comp |
|0x13  |umul |umul |umul |umul |umul | umul |
|0x14  |udiv |udiv |udiv |udiv |udiv | udiv |
|0x10  |     |     |     |store|store|store |
|0x11  |     |     |     |     |     | addr |
|0x20  |     |     |     |swap |rmove|rmove |
|0x21  |     |     |     |     |radd | radd |
|0x22  |     |     |     |     |rsub | rsub |
|0x23  |     |     |     |     |rsmul|rsmul |
|0x24  |     |     |     |     |rsdiv|rsdiv |
|0x25  |     |     |     |     |rcomp|rcomp |
|0x33  |     |     |     |     |rumul|rumul |
|0x34  |     |     |     |     |rudiv|rudiv |
|0x80  |jump |jump |jump |jump |jump | jump |
|0x81  | jeq | jeq | jeq | jeq | jeq | jeq  |
|0x82  |jneq |jneq |jneq |jneq |jneq | jneq |
|0x83  | sjl | sjl | sjl | sjl | sjl | sjl  |
|0x84  |sjgeq|sjgeq|sjneq|sjgeq|sjgeq|sjgeq |
|0x85  |sjleq|sjleq|sjleq|sjleq|sjleq|sjleq |
|0x86  | sjg | sjg | sjg | sjg | sjg | sjg  |
|0x93  | ujl | ujl | ujl | ujl | ujl | ujl  |
|0x94  |ujgeq|ujgeq|ujgeq|ujgeq|ujgeq|ujgeq |
|0x95  |ujleq|ujleq|ujleq|ujleq|ujleq|ujleq |
|0x96  | ujg | ujg | ujg | ujg | ujg | ujg  |
|0x99  |halt |halt |halt |halt |halt | halt |

На самом деле операция `div` запускает в АЛУ схему `divmod`.

Ниже дана таблица команд условных переходов.
Откуда берутся операнды для сравнения зависит от архитектуры модельной
машины. Подробнее смотри *[1]*.

|Мнемонический код|Условие перехода|Описание                         |
|:----------------|:--------------:|:--------------------------------|
|jeq              |      ==        |jump if equal                    |
|jneq             |      !=        |jump if not equal                |
|sjl              |     <  s       |signed jump if less              |
|sjgeq            |     >= s       |signed jump if greater or equal  |
|sjleq            |     <= s       |signed jump if less or equal     |
|sjg              |     >  s       |signed jump if greater           |
|ujl              |     <  u       |unsigned jump if less            |
|ujgeq            |     >= u       |unsigned jump if greater or equal|
|ujleq            |     <= u       |unsigned jump if less or equal   |
|ujg              |     >  u       |unsigned jump if greater         |

## Описание модельных машин

<details>

  <summary>Псевдокод</summary>

  Для описание команд в тексте ниже используется псевдокод:
  * `R_M` - регистр с номером `M`
  * `R` - для краткости регистр с номером `R` записывается просто `R` вместо `R_R`
  * `[A]` - ячейка оперативной памяти;
    адрес рассчитывается по модулю размера оперативной памяти (`2^16`)
  * `R := [A]` - загрузка данных по адресу `A` из ram в регистр `R`
  * `[A] := R` - сохранение данных из регистра `R` по адресу `A` в ram
  * `S := R1 op R2` - вычислить операцию `op` и сохранить результат в регистр `S`
  * `calc R1 op R2` - вычислить операцию `op` и не сохранять результат
  * `S := R1 op R2 and set FLAGS`, `calc R1 op R2 and set FLAGS` - то же самое +
    выставить регистр `FLAGS` в зависимости от результата вычислений
  * `op(FLAGS)` - условие вычисляется исходя из регистра `FLAGS`
  * `if C then X` - действие `X` происходит если выполнено условие `C`
  * `X; Y` - действия `X` и `Y` происходят параллельно
  * Описание команды состоит из трех шагов, происходящих последовательно:
    - load: `X`
    - exec: `Y`
    - write back: `Z`
  * Для краткости описание может быть сокращено до одного или двух шагов,
    если детали реализации не имеют значения.

</details>

<details>

  <summary>Ошибочные ситуации</summary>

  В случае ошибочной ситуации машина будет остановлена и вывод производится
  не будет.

  Ячейка оперативной памяти может быть меньше размера операнда или команды.
  Возможна ситуация, при которой процессор попытается
  считать или записать данные за границей доступных адресов оперативной
  памяти. Например при исполнении команды `move 0000 ffff`.
  Такая ситуация является ошибочной ситуацией.
  Деления на ноль является ошибочной ситуацией.

</details>

### mm-3

Архитектура трехадресной модельной машины.

* Размер ячейки оперативной памяти: 7 байт.
* Размер адреса: 2 байта.
* Арифметические вычисления производятся с одной ячейкой оперативной памяти.
* Код команды помещается в одну ячейку оперативной памяти `COP А1 А2 А3`.
* Регистры: `S`, `R1`, `R2`, `FLAGS`, `PC`, `IR`, `ADDR`.

#### Назначение регистров

* `S` - регистр сумматор, в него записывается результат арифметической операции.
* `R1`, `R2` - регистры операндов арифметических операций.
* `FLAGS` - регистр флагов.
* `PC` - регистр указатель инструкции.
* `IR` - регистр для хранения инструкции.
* `ADDR` - регистр для хранения адреса для инструкции перехода.

#### Описание команд

* `add`, `sub`, `smul`, `umul`:
    - load: `R1 := [A1]; R2 := [A2]`
    - exec: `S := R1 op R2 and set FLAGS`
    - write back: `[A3] := S`
* `sdiv`, `udiv`:
    - load: `R1 := [A1]; R2 := [A2]`
    - exec: `S := R1 / R2 and set FLAGS; R1 := R1 % R2`
    - write back: `[A3] := S; [A3 + 1] := R1`
* `jump`: `PC := A3`
* `jeq`, `jneq`, `jl`, `jleq`, `jg`, `jgeq`:
    - load: `R1 := [A1]; R2 := [A2]`
    - exec: `S := R1 - R2 and set FLAGS`
    - write back: `if op(FLAGS) then PC := A3`
* `move`: `[A3] := [A1]`
* `halt`: `FLAGS := HALT`

### mm-2

Архитектура двухадресной модельной машины.

* Размер ячейки оперативной памяти: 5 байт.
* Размер адреса: 2 байта.
* Арифметические вычисления производятся с одной ячейкой оперативной памяти.
* Код команды помещается в одну ячейку оперативной памяти `COP А1 А2`.
* Регистры: `R1`, `R2`, `FLAGS`, `PC`, `IR`, `ADDR`.

#### Описание команд

* `add`, `sub`, `smul`, `umul`:
    - load: `R1 := [A1]; R2 := [A2]`
    - exec: `R1 := R1 op R2 and set FLAGS`
    - write back: `[A1] := R1`
* `sdiv`, `udiv`:
    - load: `R1 := [A1]; R2 := [A2]`
    - exec: `R1 := R1 / R2 and set FLAGS; R2 := R1 % R2`
    - write back: `[A1] := R1; [A1 + 1] := R2`
* `jump`: `PC := A2`
* `cmp`:
    - load: `R1 := [A1]; R2 := [A2]`
    - exec: `R1 := R1 - R2 and set FLAGS`
* `jeq`, `jneq`, `jl`, `jleq`, `jg`, `jgeq`: `if op(FLAGS) then PC := A2`
* `move`: `[A1] := [A2]`
* `halt`: `FLAGS := HALT`

### mm-v

Архитектура модельной машины с переменным (variable) форматом команд.

* Размер ячейки оперативной памяти: 1 байт.
* Размер адреса: 2 байта.
* Арифметические вычисления производятся со словами в 5 ячеек оперативной
  памяти.
* Код команды занимает разное количество ячеек в зависимости от выполняемой
  операции.
* Регистры: `R1`, `R2`, `FLAGS`, `PC`, `IR`, `ADDR`.

#### Таблица кодов команд

|Код команды|Мнемоник|Формат    |Длина (в байтах)|
|:----------|:------:|:---------|---------------:|
|0x00       |move    |move A1 A2|               5|
|0x01       |add     |add  A1 A2|               5|
|0x02       |sub     |sub  A1 A2|               5|
|0x03       |smul    |smul A1 A2|               5|
|0x04       |sdiv    |sdiv A1 A2|               5|
|0x05       |comp    |comp A1 A2|               5|
|0x13       |umul    |umul A1 A2|               5|
|0x14       |udiv    |udiv A1 A2|               5|
|0x80       |jump    |jump  A1  |               3|
|0x81       |jeq     |jeq   A1  |               3|
|0x82       |jneq    |jneq  A1  |               3|
|0x83       |sjl     |sjl   A1  |               3|
|0x84       |sjgeq   |sjgeq A1  |               3|
|0x85       |sjleq   |sjleq A1  |               3|
|0x86       |sjg     |sjg   A1  |               3|
|0x93       |ujl     |ujl   A1  |               3|
|0x94       |ujgeq   |ujgeq A1  |               3|
|0x95       |ujleq   |ujleq A1  |               3|
|0x96       |ujg     |ujg   A1  |               3|
|0x99       |halt    |halt      |               1|

#### Описание команд

* `add`, `sub`, `smul`, `umul` - format `op A1 A2`:
    - load: `R1 := [A1]; R2 := [A2]`
    - exec: `R1 := R1 op R2 and set FLAGS`
    - write back: `[A1] := R1`
* `sdiv`, `udiv` - format `op A1 A2`:
    - load: `R1 := [A1]; R2 := [A2]`
    - exec: `R1 := R1 / R2 and set FLAGS; R2 := R1 % R2`
    - write back: `[A1] := R1; [A1 + 1] := R2`
* `jump A1`: `PC := A1`
* `cmp A1 A2`:
    - load: `R1 := [A1]; R2 := [A2]`
    - exec: `R1 := R1 - R2 and set FLAGS`
* `jeq`, `jneq`, `jl`, `jleq`, `jg`, `jgeq` - format `op A`: `if op(FLAGS) then PC := A`
* `move A1 A2`: `[A1] := [A2]`
* `halt`: `FLAGS := HALT`

### mm-1

Архитектура одноадресной модельной машины.

* Размер ячейки оперативной памяти: 3 байта.
* Размер адреса: 2 байта.
* Арифметические вычисления производятся с одной ячейкой оперативной памяти.
* Код команды помещается в одну ячейку оперативной памяти `COP А`.
* Регистры: `S`, `R`, `S1`, `FLAGS`, `PC`, `IR`.

Регистры `S` и `S1` хранят информацию постоянно, а не заполняются при
выполнении очередной команды, как в предыдущих машинах.
В регистр `R` загружается операнд для арифметических операций.

#### Описание команд

* `add`, `sub`, `smul`, `umul`:
    - load: `R := [A]`
    - exec: `S := S op R and set FLAGS`
* `sdiv`, `udiv`:
    - load: `R := [A]`
    - exec: `S := S / R and set FLAGS; S1 := S % R`
* `jump A`: `PC := A`
* `cmp`:
    - load: `R := [A]`
    - exec: `calc S - r and set FLAGS`
* `jeq A`, `jneq`, `jl`, `jleq`, `jg`, `jgeq`: `if op(FLAGS) then PC := A`
* `load A`: `S := [A]`
* `store A`: `[A] := S`
* `swap`: `S := S1; S1 := S`
* `halt`: `FLAGS := HALT`

### mm-r

Архитектура модельной машины с регистрами (registers)

* Размер ячейки оперативной памяти: 2 байта.
* Размер адреса: 2 байта.
* Арифметические вычисления производятся со словом в 4 байта.
* Код команды занимает разное количество ячеек в зависимости от выполняемой
  операции. Арифметические команды имеют формы регистр-регистр и регистр-память.
  Команды регистр-регистр имеют формат `COP RA1 RA2` и занимают 2 байта.
  Команды регистр-память имеют формат `COP R 0 A` и занимают 4 байта.
  Команды перехода имеют формат `COP 0 0 A` и занимают 4 байта.
* Регистры: `R0-RF`, `S`, `S1`, `FLAGS`, `PC`, `IR`.

Основное отличие этой машины от предыдущих - наличие адресуемых регистров
общего назначения `R0-RF`, используемых для арифметических
вычислений и адресации памяти.
`R0` - специальный регистр, всегда содержащий 0, что бы ни было в него записано
предыдущей командой. `S`, `S1` - неадресуемые регистры для работы АЛУ.

#### Таблица кодов команд

|Код команды|Мнемоник|Формат     |Длина (в байтах)|
|:----------|:------:|:----------|---------------:|
|0x00       |load    |load R 0 A |               4|
|0x01       |add     |add R 0 A  |               4|
|0x02       |sub     |sub R 0 A  |               4|
|0x03       |smul    |smul R 0 A |               4|
|0x04       |sdiv    |sdiv R 0 A |               4|
|0x05       |comp    |comp R 0 A |               4|
|0x13       |umul    |umul R 0 A |               4|
|0x14       |udiv    |udiv R 0 A |               4|
|0x10       |store   |store R 0 A|               4|
|0x20       |rmove   |rmove RX RY|               2|
|0x21       |radd    |radd RX RY |               2|
|0x22       |rsub    |rsub RX RY |               2|
|0x23       |rsmul   |rsmul RX RY|               2|
|0x24       |rsdiv   |rsdiv RX RY|               2|
|0x25       |rcomp   |rcomp RX RY|               2|
|0x33       |rumul   |rumul RX RY|               2|
|0x34       |rudiv   |rudiv RX RY|               2|
|0x80       |jump    |jump 00 A  |               4|
|0x81       |jeq     |jeq 00 A   |               4|
|0x82       |jneq    |jneq 00 A  |               4|
|0x83       |sjl     |sjl 00 A   |               4|
|0x84       |sjgeq   |sjgeq 00 A |               4|
|0x85       |sjleq   |sjleq 00 A |               4|
|0x86       |sjg     |sjg 00 A   |               4|
|0x93       |ujl     |ujl 00 A   |               4|
|0x94       |ujgeq   |ujgeq 00 A |               4|
|0x95       |ujleq   |ujleq 00 A |               4|
|0x96       |ujg     |ujg 00 A   |               4|
|0x99       |halt    |halt 00    |               2|

#### Описание команд

* register-memory `add`, `sub`, `smul`, `umul` - format `op R 0 A`:
    - load: `S := R; S1 := [A]`
    - exec: `S := S op S1 and set FLAGS`
    - write back: `R := S`
* register-memory `sdiv`, `udiv` - format `op R 0 A`,
  `R_next` - регистр, следующий за регистром `R`; за `RF` следует `R0`:
    - load: `S := R; S1 := [A]`
    - exec: `S := S / S1 and set FLAGS; S1 := S % S1`
    - write back:   `R, R_next := S, S1`
* register-memory `comp R 0 A`:
    - load: `S := S; S1 := [A]`
    - exec: `S := S - S1 and set FLAGS`
* `load R 0 A`: `R := [A]`
* `store R 0 A`: `[A] := R`
* register-register `radd`, `rsub`, `rsmul`, `rumul` - format `op X Y`:
    - load: `S := R_X; S1 := R_Y`
    - exec: `S := S op S1 and set FLAGS`
    - write back: `R_X := S`
* register-register `rsdiv`, `rudiv` - format `op X Y`:
    - load: `S := R_X; S1 := R_Y`
    - exec: `S := S / S1 and set FLAGS; S1 := S % S1`
    - write back: `R_X := S; R_next := S1`
* register-register `rcomp X Y`:
    - load: `S := R_X; S1 := R_Y`
    - exec: `S := S - S1 and set FLAGS`
* register-register `rmove X Y`: `R_X := R_Y`
* `jump A`: `PC := A`
* `jeq`, `jneq`, `jl`, `jleq`, `jg`, `jgeq` - format `op 00 A`: `if op(FLAGS) then PC := A`
* `halt`: `FLAGS := HALT`

### mm-m

Архитектура модельной машины с модификацией адресов (modification).

* Размер ячейки оперативной памяти: 2 байта.
* Размер адреса: 2 байта.
* Арифметические вычисления производятся со словом в 4 байта.
* Код команды занимает разное количество ячеек в зависимости от выполняемой
  операции. Арифметические команды имеют формы регистр-регистр и регистр-память.
  Команды регистр-регистр имеют формат `COP RA1 RA2` и занимают 2 байта.
  Команды регистр-память имеют формат `COP R M A` и занимают 4 байта.
  Команды перехода имеют формат `COP 0 0 A` и занимают 4 байта.
* Регистры: `R0-RF`, `S`, `S1`, `FLAGS`, `PC`, `IR`.

Является расширением модельной машины с регистрами.

Адресация данных теперь производится таким алгоритмом:

1. Возьмем содержимое адресуемого регистра с номером `M` (от 0x0 до 0xF): `R_M`.
   Если номер регистра `M` равен нулю, значение `R_M` также равно нулю вне
   зависимости от содержимого регистра `R0`.
2. Добавим к нему адрес `A` (от 0x0000 до 0xFFFF): `R_M + A`.
3. Возьмем остаток от деления этого адреса на 2^16: `(R_M + A) % 2^16`.
4. Возьмем из ОЗУ данные по полученному адресу: `[R_M + A]`.

#### Таблица кодов команд

|Код команды|Мнемоник|Формат     |Длина (в байтах)|
|:----------|:------:|:----------|---------------:|
|0x00       |load    |load R M A |               4|
|0x01       |add     |add R M A  |               4|
|0x02       |sub     |sub R M A  |               4|
|0x03       |smul    |smul R M A |               4|
|0x04       |sdiv    |sdiv R M A |               4|
|0x05       |comp    |comp R M A |               4|
|0x11       |addr    |addr R M A |               4|
|0x13       |umul    |umul R M A |               4|
|0x14       |udiv    |udiv R M A |               4|
|0x10       |store   |store R M A|               4|
|0x20       |rmove   |rmove RX RY|               2|
|0x21       |radd    |radd RX RY |               2|
|0x22       |rsub    |rsub RX RY |               2|
|0x23       |rsmul   |rsmul RX RY|               2|
|0x24       |rsdiv   |rsdiv RX RY|               2|
|0x25       |rcomp   |rcomp RX RY|               2|
|0x33       |rumul   |rumul RX RY|               2|
|0x34       |rudiv   |rudiv RX RY|               2|
|0x80       |jump    |jump 0 M A |               4|
|0x81       |jeq     |jeq 0 M A  |               4|
|0x82       |jneq    |jneq 0 M A |               4|
|0x83       |sjl     |sjl 0 M A  |               4|
|0x84       |sjgeq   |sjgeq 0 M A|               4|
|0x85       |sjleq   |sjleq 0 M A|               4|
|0x86       |sjg     |sjg 0 M A  |               4|
|0x93       |ujl     |ujl 0 M A  |               4|
|0x94       |ujgeq   |ujgeq 0 M A|               4|
|0x95       |ujleq   |ujleq 0 M A|               4|
|0x96       |ujg     |ujg 0 M A  |               4|
|0x99       |halt    |halt 00    |               2|

#### Описание команд

* `addr R M A`: `R := R_M + A`
* register-memory `add`, `sub`, `smul`, `umul` - format `op R M A`:
    - load: `S := R; S1 := [R_M + A]`
    - exec: `S := S op S1 and set FLAGS`
    - write back: `R := S`
* register-memory `sdiv`, `udiv` - format `op R M A`,
  `R_next` - регистр, следующий за регистром `R`; за `RF` следует `R0`:
    - load: `S := R; S1 := [R_M + A]`
    - exec: `S := S / S1 and set FLAGS; S1 := S % S1`
    - write back:   `R, R_next := S, S1`
* register-memory `comp R M A`:
    - load: `S := S; S1 := [R_M + A]`
    - exec: `S := S - S1 and set FLAGS`
* `load R M A`: `R := [R_M + A]`
* `store R M A`: `[R_M + A] := R`
* register-register `radd`, `rsub`, `rsmul`, `rumul` - format `op X Y`:
    - load: `S := R_X; S1 := R_Y`
    - exec: `S := S op S1 and set FLAGS`
    - write back: `R_X := S`
* register-register `rsdiv`, `rudiv` - format `op X Y`:
    - load: `S := R_X; S1 := R_Y`
    - exec: `S := S / S1 and set FLAGS; S1 := S % S1`
    - write back: `R_X := S; R_next := S1`
* register-register `rcomp X Y`:
    - load: `S := R_X; S1 := R_Y`
    - exec: `S := S - S1 and set FLAGS`
* register-register `rmove X Y`: `R_X := R_Y`
* `jump A`: `PC := R_M + A`
* `jeq`, `jneq`, `jl`, `jleq`, `jg`, `jgeq` - format `op 0 M A`: `if op(FLAGS) then PC := R_M + A`
* `halt`: `FLAGS := HALT`

#### Язык ассемблера

Для машины с модификацией адресов поддерживается ассемблер.
Ассемблер нечувствителен к регистру. Команды компилятору предворяются точкой.
Доступные команды компилятора:

- `.config число` - дальнейшие команды и данные располагать начиная с адреса
  `число`.
- `.code` - дальше идет исходный код, который нужно располагать начиная с
  адреса `0x00`.
- `.word список_чисел` - разместить список чисел в памяти как есть, каждое
  число занимает пару ячеек.
- `.dump имя_метки` - по завершении работы программы вывести содержимое памяти
  по адресу `имя_метки`, команда выводит содержимое двух ячеек как одно число.
  Для вывода массива фиксированного размера используйте формат
  `.dump имя_метки(размер)`. Также метки для вывода можно перечислять через
  запятую. Например: `.dump array(5), sum`

Коды команд те же, что и в таблице кодов `mmm`. Имя метки - последовательность
английских букв, цифр и знака `_`, первый символ последовательности - не цифра.
Адрес представляет собой либо имя метки, либо строку вида
`имя_метки(имя_регистра)`, где `имя_регистра` - одно из значений `R0-RF`.

Ввод данных не поддерживается.

    .config 0x100
    sum: .word 0
    array: .word -1, 2, 3, 4, 5
    zero: .word 0
    size_word: .word 2
    size_array: .word 10
    .dump array(5), sum
    .code
    load R2, size_word
    load RF, size_array
    load R5, zero
    rsub R6, R6
    rpt: add R5, array(R6)
    radd R6, R2
    rcomp R6, RF
    jneq rpt
    store R5, sum
    halt


## See also

- [Implementation](docs/implementation.md)
- [Development](docs/development.md)
- [Todo list](docs/todo.md)

## References

1. [E. А. Бордаченкова - Модельные ЭВМ](docs/references/ModComp.pdf)
2. [Е. А. Бордаченкова - Архитектура ЭВМ. Учебные машины. Методическое пособие](docs/references/bordachenkova.architecture.model.machines.2010.doc)
3. [В. Г. Баула - Введение в архитектуру ЭВМ и системы программирования](docs/references/baula.intro.pdf)
4. [Учебная трёхадресная машина УМ-3](docs/references/um3.command.set.html)
5. [Сборник упражнений по учебным машинам](docs/references/um3.tasks.html)

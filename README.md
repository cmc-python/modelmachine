# modelmachine
Model machine emulator

## TODO

* УМ-2 (двухадресная)
* УМ-П (с переменным форматом команд)
* УМ-1 (одноадресная)
* УМ-С (стековая)
* УМ-Р (решистровая)
* УМ с модификацией адресов ???

* Работа с плавающей запятой
* Подумать о mock в тестах
* ГУИ

## Списки

Что делает контролирующее устройство?

1. В регистр команды (РК) записывается содержимое ячейки, адрес
   которой находится в регистре СА.
2. Значение СА увеличивается на 1, так что теперь СА указывает на
   следующую команду программы.
3. Устройство управления расшифровывает команду, находящуюся в
   РК, и организует её выполнение. Как именно выполняется команда, зависит
   от вида самой команды.

Как работает ЦП?

1. Fetching the instruction: The next instruction is fetched from the memory
   address that is currently stored in the program counter (PC), and stored
   in the instruction register (IR). At the end of the fetch operation,
   the PC points to the next instruction that will be read at the next cycle.
2. Decode the instruction: During this cycle the encoded instruction
   present in the IR (instruction register) is interpreted by the decoder.
3. Read the effective address: In case of a memory instruction
   (direct or indirect) the execution phase will be in the next clock pulse.
   If the instruction has an indirect address, the effective address is read
   from main memory, and any required data is fetched from main memory to be
   processed and then placed into data registers (Clock Pulse: T3).
   If the instruction is direct, nothing is done at this clock pulse.
   If this is an I/O instruction or a Register instruction, the operation
   is performed (executed) at clock Pulse.
4. Execute the instruction: The control unit of the CPU passes
   the decoded information as a sequence of control signals to the relevant
   function units of the CPU to perform the actions required by
   the instruction such as reading values from registers, passing them
   to the ALU to perform mathematical or logic functions on them,
   and writing the result back to a register. If the ALU is involved,
   it sends a condition signal back to the CU. The result generated
   by the operation is stored in the main memory, or sent to an output device.
   Based on the condition of any feedback from the ALU,
   Program Counter may be updated to a different address from which
   the next instruction will be fetched.

Инструкции модельных машин.

|OPCODE|mm-3|
|-----:|:--:|
|  0x00|move|
|  0x01|add |
|  0x02|sub |
|  0x03|smul|
|  0x04|sdiv|
|  0x13|umul|
|  0x14|udiv|
|  0x80|jump|
|  0x81| =  |
|  0x82| != |
|  0x83|< s |
|  0x84|>= s|
|  0x85|<= s|
|  0x86|> s |
|  0x93|< u |
|  0x94|>= u|
|  0x95|<= u|
|  0x96|> u |
|  0x99|halt|


### mm-3

Действия процессора для арифметических инструкций `КОП A1 A2 A3`:

1. Загрузить содержимое ячейки оперативной памяти с адресом `А1` в
   регистр `R1`.
2. Загрузить содержимое ячейки оперативной памяти с адресом `А2` в
   регистр `R2`.
3. Запустить в АЛУ электронную схему, реализующую операцию,
   задаваемую `КОП`.
4. Записать результат из регистра `S` в ячейку оперативной памяти с
   адресом `А3`.
   Если выполняется операция деления, в оперативную память записываются
   два результата: частное – в ячейку с адресом `А3`, остаток – в следующую
   ячейку, по адресу `(А3+1) mod 16^4`.

* `JMP A1 A2 A3`: IP := A3
* Условные переходы: сравниваются `R1` и `R2`, в зависимости от результата
  происходит `IP := A3`.
* Команда пересылки `move`: [A3] := R1.

## Модельная машина

Модельная машина - это чистая архитектурная концепция, позволяющая понять
логику функционирования центральных процессоров. По своей структуре она близка
к компьютерам первого поколения. Подробнее читайте по ссылкам внизу.

## Внутреннее устройство

Данная реализация модельной машины состоит из классов, разбитых на
файлы-модули:

* `memory.py` - память; делится на два класса: `регистровая` и `оперативная`;
  оперативная делится на `little-endian` и `big-endian`
* `numeric.py` - целочисленная арифметика с фиксированным числом двоичных
  знаков
* `alu.py` - арифметико-логическое устройство, работает с четко
  специализированными регистрами: `R1`, `R2`, `S`, `FLAGS` и `IP`.
* `cu.py` *не реализованно* - контролирующее устройство, выполняющее считывание команд из памяти
  и запускающее необходимые методы в арифметико-логическом устройстве
* `io.py` *не реализованно* - устройство ввода-вывода
* `cpu.py` *не реализованно* - финальное объединение устройств в единое целое

### memory.py

`AbstractMemory` - класс абстрактной памяти, предоставляющий интерфейс для
надежной связи частей компьютера. Основные методы: `fetch` и `put`, которые
принимаютна вход адрес в памяти и количество битов, с которыми нужно работать,
количество должно быть кратно размеру ячейки (слова). Строго
рекомендуется их использовать во всех унаследованных классах.

`RandomAccessMemory` - класс, реализующий память прямого доступа. При
инициализации указывается размер машинного слова и количество этих слов. Если
`is_protected=True`, то при попытке считывания из неинициализированной ячейки
будет выброшено исключение, иначе, метод `fetch` вернет нуль.

`RegisterMemory` - класс, реализующий регистровую память. При инициализации
ему дается список регистров. По умолчанию регистры заполняются нулями.

### numeric.py

Класс Integer реализует целочисленную арифметику фиксированной длины.
Поддерживаемые операторы: `+`, `-`, `*`, `/`, `%`, `==`, `!=`. Плюс методы
`get_value` и `get_data`. Деление работает согласно такому алгоритму:

    div = abs(a) // abs(b)
    if a * b < 0: div *= -1
    mod = a - b * div

## References

* E. А. Бордаченкова - "Модельные ЭВМ" <http://al.cs.msu.su/files/ModComp.pdf>
* Е. А. Бордаченкова - "Архитектура ЭВМ. Учебные машины. Методическое пособие"
  <http://al.cs.msu.su/files/bordachenkova.architecture.model.machines.2010.doc>
* В. Г. Баула - "Введение в архитектуру ЭВМ и системы программирования"
  <http://arch.cs.msu.ru/Page2.htm>
* <http://cmcmsu.no-ip.info/1course/um3.command.set.htm>

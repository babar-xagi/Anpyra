"""Independent small DEX executor for event/state tests, never shipped in an APK.

This checks emitted instructions/branches and native-call contracts. It is not
an ART verifier; the separate real-device suite covers Android acceptance.
"""

import struct


def uleb(data, pos):
    value, shift = 0, 0
    while True:
        byte = data[pos]
        pos += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, pos
        shift += 7


def integer(value):
    return (int(value) + 0x80000000) % 0x100000000 - 0x80000000


class Widget:
    def __init__(self, text=""):
        self.text, self.enabled, self.color, self.reads = text, True, None, 0


class Instance:
    def __init__(self):
        self.fields, self.recreated = {}, False


class DexRuntime:
    def __init__(self, data):
        self.data = data

        def u32(pos):
            return struct.unpack_from("<I", data, pos)[0]

        strings = []
        for index in range(u32(56)):
            _, pos = uleb(data, u32(u32(60) + index * 4))
            raw = data[pos : data.index(0, pos)].replace(b"\xc0\x80", b"\x00")
            decoded = raw.decode("utf-8", "surrogatepass")
            strings.append(
                decoded.encode("utf-16-le", "surrogatepass").decode("utf-16-le", "surrogatepass")
            )
        self.strings = strings
        types = [strings[u32(u32(68) + i * 4)] for i in range(u32(64))]
        self.fields = []
        for index in range(u32(80)):
            owner, typ, name = struct.unpack_from("<HHI", data, u32(84) + 8 * index)
            self.fields.append((types[owner], strings[name], types[typ]))
        self.methods = []
        for index in range(u32(88)):
            owner, proto, name = struct.unpack_from("<HHI", data, u32(92) + 8 * index)
            self.methods.append((types[owner], strings[name]))
        self.codes = {}
        for index in range(u32(96)):
            pos = u32(u32(100) + 32 * index + 24)
            counts = []
            for _ in range(4):
                count, pos = uleb(data, pos)
                counts.append(count)
            for count in counts[:2]:
                for _ in range(count):
                    _, pos = uleb(data, pos)
                    _, pos = uleb(data, pos)
            for count in counts[2:]:
                method = 0
                for _ in range(count):
                    delta, pos = uleb(data, pos)
                    _, pos = uleb(data, pos)
                    code, pos = uleb(data, pos)
                    method += delta
                    self.codes[method] = code

    def call(self, name, instance, *args):
        candidates = [i for i in self.codes if self.methods[i][1] == name]
        assert len(candidates) == 1, candidates
        return self.execute(candidates[0], (instance, *args))

    def invoke(self, method, args):
        if method in self.codes:
            return self.execute(method, args)
        owner, name = self.methods[method]
        if name == "getText":
            args[0].reads += 1
            return args[0].text
        if name == "toString":
            return str(args[0])
        if name == "valueOf":
            return str(integer(args[0]))
        if name == "concat":
            return args[0] + args[1]
        if name == "equals":
            return int(args[0] == args[1])
        if name == "isEmpty":
            return int(args[0] == "")
        if name == "setText":
            args[0].text = args[1]
        elif name == "setEnabled":
            args[0].enabled = bool(args[1])
        elif name == "isEnabled":
            return int(args[0].enabled)
        elif name == "setTextColor":
            args[0].color = integer(args[1])
        elif name == "recreate":
            args[0].recreated = True
        elif name == "containsKey":
            return int(args[1] in args[0])
        elif name in {"putInt", "putBoolean", "putString"}:
            args[0][args[1]] = args[2]
        elif name in {"getInt", "getBoolean", "getString"}:
            return args[0].get(args[1])
        elif owner == "Landroid/app/Activity;" and name == "onSaveInstanceState":
            pass
        else:
            raise AssertionError((owner, name, args))
        return None

    def execute(self, method, args):
        code = self.codes[method]
        registers, inputs, _, _, _, length = struct.unpack_from("<HHHHII", self.data, code)
        words = struct.unpack_from("<" + "H" * length, self.data, code + 16)
        values = [None] * registers
        assert len(args) == inputs
        values[registers - inputs :] = args
        pc, result, steps = 0, None, 0

        def zero(value):
            return value is None or (isinstance(value, (int, bool)) and value == 0)

        def delta(word):
            return word - 65536 if word >= 32768 else word

        while pc < length:
            steps += 1
            assert steps < 10000, "unexpected bytecode loop"
            word, op = words[pc], words[pc] & 255
            a = word >> 8
            if op in {0x02, 0x08}:
                values[a] = values[words[pc + 1]]
                pc += 2
            elif op in {0x0A, 0x0C}:
                values[a] = result
                pc += 1
            elif op == 0x0E:
                return None
            elif op == 0x0F:
                return values[a]
            elif op == 0x12:
                value = word >> 12
                values[(word >> 8) & 15] = value - 16 if value >= 8 else value
                pc += 1
            elif op == 0x13:
                values[a] = delta(words[pc + 1])
                pc += 2
            elif op == 0x14:
                values[a] = integer(words[pc + 1] | words[pc + 2] << 16)
                pc += 3
            elif op == 0x1A:
                values[a] = self.strings[words[pc + 1]]
                pc += 2
            elif op in {0x52, 0x54, 0x55, 0x59, 0x5B, 0x5C}:
                val, owner = (word >> 8) & 15, word >> 12
                name = self.fields[words[pc + 1]][1]
                if op in {0x52, 0x54, 0x55}:
                    values[val] = values[owner].fields[name]
                else:
                    values[owner].fields[name] = values[val]
                pc += 2
            elif op == 0x29:
                pc += delta(words[pc + 1])
            elif 0x32 <= op <= 0x38:
                if op == 0x38:
                    take = zero(values[a])
                else:
                    left, right = values[(word >> 8) & 15], values[word >> 12]
                    equal = left == right if isinstance(left, (int, bool)) else left is right
                    take = {
                        0x32: lambda: equal,
                        0x33: lambda: not equal,
                        0x34: lambda: left < right,
                        0x35: lambda: left >= right,
                        0x36: lambda: left > right,
                        0x37: lambda: left <= right,
                    }[op]()
                pc += delta(words[pc + 1]) if take else 2
            elif op in {0x6E, 0x6F, 0x70, 0x71}:
                packed = words[pc + 2]
                regs = [(packed >> shift) & 15 for shift in (0, 4, 8, 12)] + [(word >> 8) & 15]
                result = self.invoke(words[pc + 1], tuple(values[i] for i in regs[: word >> 12]))
                pc += 3
            elif op in {0x90, 0x91}:
                left, right = values[words[pc + 1] & 255], values[words[pc + 1] >> 8]
                values[a] = integer(left + right if op == 0x90 else left - right)
                pc += 2
            else:
                raise AssertionError((self.methods[method], pc, hex(op)))
        raise AssertionError("method fell through without a return")

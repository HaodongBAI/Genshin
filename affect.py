from collections import OrderedDict

quantities = OrderedDict([(1, 0.8 / 9.5), (2, 1.6 / 12), (4, 3.2 / 17)])

type = {'Fire', 'Water', 'Grass', 'Elect', 'Wind', 'Ice', 'Rock', 'Freeze'}

interval = 0.1


class Affect:
    def __init__(self, q0, speed_config, type):
        self.q = q0
        self.speed_config = speed_config
        self.type = type

    def speed(self, t):
        if type == 'Freeze':
            return 0.4 + 0.1 * (t - self.speed_config['t0'])

        else:
            return quantities[self.speed_config['quantity_level']]

    def consume(self, q):
        self.q -= q
        return self

    def __repr__(self):
        return f"Affect(type={self.type}, q={round(self.q, 1)})"


class State:
    def __init__(self, affects):
        self.affects = affects

    def get_types(self):
        return [a.type for a in self.affects]

    def __repr__(self):
        return f"State({self.affects})"

    def get_affect_with_type(self, type):
        affects = [a for a in self.affects if a.type == type]
        if len(affects) > 0:
            return affects[0]
        else:
            return None


# Affect X Affect -> Affect
def affect_addition(A1, A2):
    assert A1.type == A2.type

    if A1.type == 'Freeze':
        return Affect(q0=A1.q + A2.q, speed_config=A1.speed_config, type=A1.type)
    else:
        return Affect(q0=max(A1.q, A2.q), speed_config=A1.speed_config, type=A1.type)


# State X State -> State
def state_addition(s1, s2):
    types = {a.type for a in s1.affects + s2.affects}

    result = State([])

    for type in types:
        a1 = s1.get_affect_with_type(type)
        a2 = s2.get_affect_with_type(type)

        if a1 is not None and a2 is not None:
            result.affects.append(affect_addition(a1, a2))
        elif a1 is not None:
            result.affects.append(a1)
        else:
            result.affects.append(a2)

    return result


# Affect X Affect -> State
def binary_reaction(A, B, t):
    tA = A.type
    tB = B.type

    qA = A.q
    qB = B.q

    if (tA, tB) in {('Water', 'Elect'), ('Elect', 'Water')}:

        if qA >= 0.4 and qB >= 0.4:
            print(f'Reaction Happened: {tA} and {tB}.')
            A.q -= 0.4
            B.q -= 0.4
        return State([a for a in [A, B] if a.q > 0])

    elif (tA, tB) in {('Water', 'Ice'), ('Ice', 'Water')}:
        print(f'Reaction Happened: {tA} and {tB}.')

        if qA < qB:
            return State([B.consume(qA), Affect(qA * 2, speed_config={'t0': t}, type='Freeze')])
        elif qA > qB:
            return State([A.consume(qB), Affect(qB * 2, speed_config={'t0': t}, type='Freeze')])
        else:
            return State([Affect(qA * 2, speed_config={'t0': t}, type='Freeze')])

    else:
        print(f'Reaction Happened: {tA} and {tB}.')

        k = get_multiplier(tA, tB)
        if qA > k * qB:
            return State([A.consume(k * qB)])
        elif qA < k * qB:
            return State([B.consume(qA / k)])
        else:
            return State([])


# State X Type -> State
def clean_latter_affect(s, type):
    types = [a.type for a in s.affects]

    if 'Freeze' in types and type in {'Ice', 'Water'}:
        return s
    elif 'Water' in types and 'Elect' in types and type in {'Water', 'Elect'}:
        return s
    else:
        return State([a for a in s.affects if a.type != type])


# State X Affect -> State
def state_reaction(s, A, time):
    orders = get_orders(s, A)

    if len(orders) == 2:
        B = s.get_affect_with_type(orders[0])
        C = s.get_affect_with_type(orders[1])
        return clean_latter_affect(
            state_reaction(
                binary_reaction(B, A, time),
                C, time
            ), A.type
        )
    elif len(orders) == 1 and len(s.affects) == 2:
        B = s.get_affect_with_type(orders[0])
        remains = State([aff for aff in s.affects if aff.type != orders[0]])
        return clean_latter_affect(
            state_addition(
                remains,
                binary_reaction(B, A, time)
            ), A.type
        )
    elif len(orders) == 1 and len(s.affects) == 1:
        B = s.get_affect_with_type(orders[0])
        return clean_latter_affect(
            binary_reaction(B, A, time),
            A.type
        )
    else:
        return State([A.consume(0.2 * A.q)])


def get_multiplier(ft, lt):
    if (ft, lt) in {
        ('Water', 'Fire'), ('Fire', 'Ice'), ('Fire', 'Freeze'),
        ('Water', 'Rock'), ('Fire', 'Rock'), ('Ice', 'Rock'), ('Elect', 'Rock'),
        ('Water', 'Wind'), ('Fire', 'Wind'), ('Ice', 'Wind'), ('Elect', 'Wind'),
    }:
        return 0.5
    elif (ft, lt) in {('Fire', 'Water'), ('Ice', 'Fire'), ('Freeze', 'Fire')}:
        return 2.0
    else:
        return 1.0


def get_orders(s, a):
    state_types = [a.type for a in s.affects]
    affect_type = a.type
    dictionary = {
        ('Water', 'Elect'): {
            'Ice': ['Elect', 'Water'],
            'Fire': ['Elect', 'Water'],
            'Wind': ['Elect', 'Water'],
            'Solid': ['Elect', 'Water'],
        },
        ('Water', 'Freeze'): {
            'Ice': ['Water'],
            'Fire': ['Freeze'],
            'Elect': ['Freeze'],
            'Wind': ['Water', 'Freeze'],
            'Solid': ['Freeze', 'Water'],
        },
        ('Ice', 'Freeze'): {
            'Water': ['Ice'],
            'Fire': ['Ice', 'Freeze'],
            'Elect': ['Ice', 'Freeze'],
            'Wind': ['Ice', 'Freeze'],
            'Solid': ['Freeze', 'Ice'],
        }
    }

    if len(state_types) == 0:
        return []
    elif len(state_types) == 1:
        return [state_types[0]]
    else:
        if tuple(state_types) not in dictionary:
            state_types = state_types[::-1]

        return dictionary[tuple(state_types)][affect_type]


# Test
def get_dummy_affect(type, quantity_level):
    return Affect(q0=quantity_level, speed_config={'quantity_level': quantity_level}, type=type)


if __name__ == '__main__':
    affects = [
        get_dummy_affect('Water', quantity_level=4),
        get_dummy_affect('Fire', quantity_level=2),
        get_dummy_affect('Ice', quantity_level=2),
        get_dummy_affect('Elect', quantity_level=5)
    ]

    s = State([])
    for affect in affects:
        s = state_reaction(s, affect, time=0)
        print(s)

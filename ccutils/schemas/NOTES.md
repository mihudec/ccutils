## Interface Schema

```
CNF | ((NOT A) OR (NOT B)) AND (A OR (NOT C)) AND (B OR (NOT D)) AND ((NOT E) OR (NOT F)) AND (E OR (NOT G))
```

[WolframAlpha](https://www.wolframalpha.com/input/?i=%28A+%3D%3E+NOT%28B%29%29+AND+%28B+%3D%3E+NOT%28A%29%29+AND+%28C+%3D%3E+A%29+AND+%28D+%3D%3E+B%29+AND+%28E+%3D%3E+NOT%28F%29%29+AND+%28F+%3D%3E+NOT%28E%29%29+AND+%28G+%3D%3E+E%29)

```json
{
    "A": {
        "keyName": "flagL2IsPresent",
        "condition": "l2 in flags"
    },
    "B": {
        "keyName": "flagL3IsPresent",
        "condition": "l3 in flags"
    },
    "C": {
        "keyName": "L2IsPresent",
        "condition": "l2 is present"
    },
    "D": {
        "keyName": "L3IsPresent",
        "condition": "l3 is present"
    },
    "E": {
        "keyName": "flagPcMemberIsPresent",
        "condition": "pc-member in flags"
    },
    "F": {
        "keyName": "flagPortChannelIsPresent",
        "condition": "port-channel in flags"
    },
    "G": {
        "keyName": "channelGroupIsPresent",
        "condition": "channel_group is present"
    } 
}
```

## Interface L2 Schema

```
(B => NOT(C)) AND (C => NOT(B)) AND (C => A) AND (D => A) AND (D => NOT(B)) AND (E => B) AND (F => B) AND (NOT(A) OR NOT(B))
```

[WolframAlpha](https://www.wolframalpha.com/input/?i=%28B+%3D%3E+NOT%28C%29%29+AND+%28C+%3D%3E+NOT%28B%29%29+AND+%28C+%3D%3E+A%29+AND+%28D+%3D%3E+A%29+AND+%28D+%3D%3E+NOT%28B%29%29+AND+%28E+%3D%3E+B%29+AND+%28F+%3D%3E+B%29+AND+%28NOT%28A%29+OR+NOT%28B%29%29)

```json
{
    "A": {
        "keyName": "modeIsAccess",
        "condition": "mode == access"
    },
    "B": {
        "keyName": "modeIsTrunk",
        "condition": "mode == trunk"
    },
    "C": {
        "keyName": "accessVlanIsPresent",
        "condition": "access_vlan is present"
    },
    "D": {
        "keyName": "voiceVlanIsPresent",
        "condition": "voice_vlan is present"
    },
    "E": {
        "keyName": "nativeVlanIsPresent",
        "condition": "native_vlan is present"
    },
    "F": {
        "keyName": "allowedVlanIsPresent",
        "condition": "allowed_vlan is present"
    }
}
```
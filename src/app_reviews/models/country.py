"""Country StrEnum with region groups and display utilities."""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar


class Country(StrEnum):
    """iTunes-supported countries as a StrEnum.

    Values are lowercase ISO 3166-1 alpha-2 codes.
    """

    AE = "ae"
    AG = "ag"
    AI = "ai"
    AL = "al"
    AM = "am"
    AO = "ao"
    AR = "ar"
    AT = "at"
    AU = "au"
    AZ = "az"
    BB = "bb"
    BE = "be"
    BF = "bf"
    BG = "bg"
    BH = "bh"
    BJ = "bj"
    BM = "bm"
    BN = "bn"
    BO = "bo"
    BR = "br"
    BS = "bs"
    BT = "bt"
    BW = "bw"
    BY = "by"
    BZ = "bz"
    CA = "ca"
    CG = "cg"
    CH = "ch"
    CL = "cl"
    CN = "cn"
    CO = "co"
    CR = "cr"
    CV = "cv"
    CY = "cy"
    CZ = "cz"
    DE = "de"
    DK = "dk"
    DM = "dm"
    DO = "do"
    DZ = "dz"
    EC = "ec"
    EE = "ee"
    EG = "eg"
    ES = "es"
    FI = "fi"
    FJ = "fj"
    FM = "fm"
    FR = "fr"
    GB = "gb"
    GD = "gd"
    GH = "gh"
    GM = "gm"
    GR = "gr"
    GT = "gt"
    GW = "gw"
    GY = "gy"
    HK = "hk"
    HN = "hn"
    HR = "hr"
    HU = "hu"
    ID = "id"
    IE = "ie"
    IL = "il"
    IN = "in"
    IS = "is"
    IT = "it"
    JM = "jm"
    JO = "jo"
    JP = "jp"
    KE = "ke"
    KG = "kg"
    KH = "kh"
    KN = "kn"
    KR = "kr"
    KW = "kw"
    KY = "ky"
    KZ = "kz"
    LA = "la"
    LB = "lb"
    LC = "lc"
    LK = "lk"
    LR = "lr"
    LT = "lt"
    LU = "lu"
    LV = "lv"
    MD = "md"
    MG = "mg"
    MK = "mk"
    ML = "ml"
    MN = "mn"
    MO = "mo"
    MR = "mr"
    MS = "ms"
    MT = "mt"
    MU = "mu"
    MW = "mw"
    MX = "mx"
    MY = "my"
    MZ = "mz"
    NA = "na"
    NE = "ne"
    NG = "ng"
    NI = "ni"
    NL = "nl"
    NP = "np"
    NO = "no"
    NZ = "nz"
    OM = "om"
    PA = "pa"
    PE = "pe"
    PG = "pg"
    PH = "ph"
    PK = "pk"
    PL = "pl"
    PT = "pt"
    PW = "pw"
    PY = "py"
    QA = "qa"
    RO = "ro"
    RU = "ru"
    SA = "sa"
    SB = "sb"
    SC = "sc"
    SE = "se"
    SG = "sg"
    SI = "si"
    SK = "sk"
    SL = "sl"
    SN = "sn"
    SR = "sr"
    ST = "st"
    SV = "sv"
    SZ = "sz"
    TC = "tc"
    TD = "td"
    TH = "th"
    TJ = "tj"
    TM = "tm"
    TN = "tn"
    TR = "tr"
    TT = "tt"
    TW = "tw"
    TZ = "tz"
    UA = "ua"
    UG = "ug"
    US = "us"
    UY = "uy"
    UZ = "uz"
    VC = "vc"
    VE = "ve"
    VG = "vg"
    VN = "vn"
    YE = "ye"
    ZA = "za"
    ZW = "zw"

    # Region group declarations (populated after class body)
    ALL: ClassVar[frozenset[Country]]
    EUROPE: ClassVar[frozenset[Country]]
    AMERICAS: ClassVar[frozenset[Country]]
    ASIA_PACIFIC: ClassVar[frozenset[Country]]
    MIDDLE_EAST: ClassVar[frozenset[Country]]
    ENGLISH_SPEAKING: ClassVar[frozenset[Country]]


# Region groups — assigned after class creation because enum members
# must be defined before they can be referenced in frozenset literals.

Country.ALL = frozenset(Country)

Country.EUROPE = frozenset(
    {
        Country.AL,
        Country.AT,
        Country.BE,
        Country.BG,
        Country.BY,
        Country.CH,
        Country.CY,
        Country.CZ,
        Country.DE,
        Country.DK,
        Country.EE,
        Country.ES,
        Country.FI,
        Country.FR,
        Country.GB,
        Country.GR,
        Country.HR,
        Country.HU,
        Country.IE,
        Country.IS,
        Country.IT,
        Country.LT,
        Country.LU,
        Country.LV,
        Country.MD,
        Country.MK,
        Country.MT,
        Country.NL,
        Country.NO,
        Country.PL,
        Country.PT,
        Country.RO,
        Country.RU,
        Country.SE,
        Country.SI,
        Country.SK,
        Country.TR,
        Country.UA,
    }
)

Country.AMERICAS = frozenset(
    {
        Country.AG,
        Country.AI,
        Country.AR,
        Country.BB,
        Country.BM,
        Country.BO,
        Country.BR,
        Country.BS,
        Country.BZ,
        Country.CA,
        Country.CL,
        Country.CO,
        Country.CR,
        Country.DM,
        Country.DO,
        Country.EC,
        Country.GD,
        Country.GT,
        Country.GW,
        Country.GY,
        Country.HN,
        Country.JM,
        Country.KN,
        Country.KY,
        Country.LC,
        Country.MX,
        Country.NI,
        Country.PA,
        Country.PE,
        Country.PY,
        Country.SR,
        Country.SV,
        Country.TC,
        Country.TT,
        Country.US,
        Country.UY,
        Country.VC,
        Country.VE,
        Country.VG,
    }
)

Country.ASIA_PACIFIC = frozenset(
    {
        Country.AU,
        Country.BN,
        Country.BT,
        Country.CN,
        Country.FJ,
        Country.FM,
        Country.HK,
        Country.ID,
        Country.IN,
        Country.JP,
        Country.KH,
        Country.KR,
        Country.KZ,
        Country.KG,
        Country.LA,
        Country.LK,
        Country.MN,
        Country.MO,
        Country.MY,
        Country.NP,
        Country.NZ,
        Country.PG,
        Country.PH,
        Country.PK,
        Country.PW,
        Country.SB,
        Country.SG,
        Country.TH,
        Country.TJ,
        Country.TM,
        Country.TW,
        Country.UZ,
        Country.VN,
    }
)

Country.MIDDLE_EAST = frozenset(
    {
        Country.AE,
        Country.BH,
        Country.DZ,
        Country.EG,
        Country.IL,
        Country.JO,
        Country.KW,
        Country.LB,
        Country.OM,
        Country.QA,
        Country.SA,
        Country.TN,
        Country.YE,
    }
)

Country.ENGLISH_SPEAKING = frozenset(
    {
        Country.AU,
        Country.CA,
        Country.GB,
        Country.IE,
        Country.NZ,
        Country.US,
        Country.ZA,
        Country.JM,
        Country.TT,
        Country.BB,
        Country.BZ,
        Country.GY,
        Country.SG,
        Country.PH,
        Country.IN,
        Country.KE,
        Country.NG,
        Country.GH,
    }
)

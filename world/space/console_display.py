from evennia import EvForm, EvTable

def display_navstat(self):

    FORMCHAR = "x"
    TABLECHAR = "c"
    FORM = '''
    .------------------------------------------------.
    |                                                |
    |  Name: xxxxx1xxxxx Player: xxxxxxx2xxxxxxx  |
    |        xxxxxxxxxxx                             |
    |                                                |
     >----------------------------------------------<
    |                                                |
    | Desc:  xxxxxxxxxxx    STR: x4x    DEX: x5x     |
    |        xxxxx3xxxxx    INT: x6x    STA: x7x     |
    |        xxxxxxxxxxx    LUC: x8x    MAG: x9x     |
    |                                                |
     >----------------------------------------------<
    |          |                                     |
    | cccccccc | ccccccccccccccccccccccccccccccccccc |
    | cccccccc | ccccccccccccccccccccccccccccccccccc |
    | cccAcccc | ccccccccccccccccccccccccccccccccccc |
    | cccccccc | ccccccccccccccccccccccccccccccccccc |
    | cccccccc | cccccccccccccccccBccccccccccccccccc |
    |          |                                     |
    -------------------------------------------------
    '''
    form = EvForm({FORMCHAR, TABLECHAR, FORM})

    # add data to each tagged form cell
    form.map(cells={1: "Tom the Bouncer",
                    2: "Griatch",
                    3: "A sturdy fellow",
                    4: 12,
                    5: 10,
                    6:  5,
                    7: 18,
                    8: 10,
                    9:  3})
    # create the EvTables
    tableA = EvTable("HP","MV","MP",
                               table=[["**"], ["*****"], ["***"]],
                               border="incols")
    tableB = EvTable("Skill", "Value", "Exp",
                               table=[["Shooting", "Herbalism", "Smithing"],
                                      [12,14,9],["550/1200", "990/1400", "205/900"]],
                               border="incols")
    # add the tables to the proper ids in the form
    form.map(tables={"A": tableA,
                     "B": tableB})

    # unicode is required since the example contains non-ascii characters
    return unicode(form)

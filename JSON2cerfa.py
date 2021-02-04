import json

from pdffunctions import PdfEditor

user = "melody"

userconf = json.load(open(f"config.{user}.sconf.json"))


def trgs(a_value):
    return [a_value[0], a_value[1] if len(a_value) == 2 else {}] if type(a_value[0]) is list else [a_value, {}]


def do_2019():
    cerfa_spacific = {
        "filename": "2086_3126.pdf",
        "name1": [87, 287, 0],
        "firstname1": [103, 305, 0],
        "postal_address1": [100, 322, 0],
        "name2": [190, 433, 0],
        "firstname2": [190, 449, 0],
        "postal_address2": [190, 467, 0],
        "total_calc": [423, 292, 1],
        "total_calc_2": [450, 361, 4],
        "grand_total_calc": [450, 462, 4]
    }
    calc_fields = {
        "211": [188, 507, 0],
        "212": [203, 543, 0],
        "213": [203, 594, 0],
        "214": [203, 610, 0],
        "215": [203, 635, 0],
        "216": [203, 660, 0],
        "217": [203, 691, 0],
        "218": [203, 723, 0],
        "220": [203, 118, 1],
        "221": [203, 150, 1],
        "222": [203, 184, 1],
        "223": [203, 218, 1],
        "224": [203, 249, 1],
    }
    for i in range(0, 5):
        cerfa_spacific.update({f"{k}.{i}": [v[0]+ 68 *  i, v[1] , v[2]] for k, v in calc_fields.items()})
    return cerfa_spacific


def place_texts(textpos, textvalues, pdfEditor):
    for key, value in textvalues.items():
        position = textpos.get(key)
        if not position:
            print(f"Warning, skipped {key} because it does not exist in textpostitons")
            continue
        new_args = trgs(position)
        pdfEditor.addText(*[str(value), *new_args[0]], **new_args[1])


def do_pdf(pdfdata):
    cessions = json.load(open(f"cessions.{user}.json", "r"))
    pdf_number = 1
    for index, cession in enumerate(cessions):
        if index % 5 > 0:
            continue

        print(f"{round(index / len(cessions) * 100)}%")
        cessions_subset = cessions[index:(index + 5)]
        monPDF = PdfEditor(pdfdata.get('filename'))
        place_texts(pdfdata, {
            "name1": userconf.get("name"),
            "firstname1": userconf.get("firstname"),
            "postal_address1": userconf.get("postal_address"),
            "name2": userconf.get("name"),
            "firstname2": userconf.get("firstname"),
            "postal_address2": userconf.get("postal_address"),
            "total_calc":round(sum([x.get("224") for x in cessions_subset]),2),
            "total_calc_2":round(sum([x.get("224") for x in cessions_subset]),2),
            "grand_total_calc":round(sum([x.get("224") for x in cessions]),2)
        }
                    , monPDF)
        for subset_index, cession in enumerate(cessions_subset):
            place_texts(pdfdata, {f"{k}.{subset_index}": round(v,2) if type(v) is float else v for k, v in cession.items() if f"{k}.{subset_index}" in pdfdata}, monPDF)

        monPDF.save_as(f"{pdf_number}.{pdfdata.get('filename')}")
        pdf_number += 1


do_pdf(do_2019())

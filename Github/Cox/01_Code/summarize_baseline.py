"""Reproduce the baseline table from the private, processed final model input."""
import argparse
from pathlib import Path
import pandas as pd


def summarize(data):
    groups = {"Overall":data, "Incident MDD (n=735)":data.loc[data.observed.eq(1)],
              "No incident MDD (n=93,801)":data.loc[data.observed.eq(0)]}
    rows = []
    def add(label, column=None, condition=None):
        row = {"Variable":label}
        for name, frame in groups.items():
            if column:
                x = frame[column]
                row[name] = f"{x.mean():.2f} ({x.std(ddof=1):.2f})"
            elif condition:
                mask = condition(frame)
                row[name] = f"{mask.sum():,} ({mask.mean()*100:.1f}%)"
            else:
                row[name] = ""
        row["Missing, n"] = 0
        rows.append(row)
    add("Age at recruitment, years; mean (SD)","Age_at_recruitment")
    add("Body mass index, kg/m²; mean (SD)","Body_mass_index")
    add("Townsend deprivation index; mean (SD)","Townsend_deprivation_index")
    for heading, categories in [
        ("Sex",[("Female",lambda d:d.Sex_c.eq(0)),("Male",lambda d:d.Sex_c.eq(1))]),
        ("Education",[("University degree",lambda d:d.Edu_c.eq(1)),("Other educational qualification",lambda d:d.Edu_c.eq(0))]),
        ("Ethnicity",[("White British",lambda d:d.Ethn_c.eq(1)),("Other ethnic backgrounds",lambda d:d.Ethn_c.eq(0))]),
        ("Employment status",[("Paid employment",lambda d:d.Emp_b.eq(0)),("Other status",lambda d:d.Emp_b.eq(1))]),
    ]:
        add(heading)
        for name, condition in categories:
            add(name,condition=condition)
    add("Average total household income before tax")
    add("<£18,000",condition=lambda d:d[[f"tax_{i}" for i in range(2,6)]].sum(axis=1).eq(0))
    for i, name in enumerate(["£18,000–30,999","£31,000–51,999","£52,000–100,000",">£100,000"],2):
        add(name,condition=lambda d,i=i:d[f"tax_{i}"].eq(1))
    add("Smoking status")
    add("Never smoker",condition=lambda d:d.Smk_b.eq(0))
    add("Previous/current smoker",condition=lambda d:d.Smk_b.eq(1))
    add("Alcohol intake frequency")
    add("Never",condition=lambda d:d[[f"alc_{i}" for i in range(1,6)]].sum(axis=1).eq(0))
    for i,name in enumerate(["Daily or almost daily","Three or four times a week","Once or twice a week","One to three times a month","Special occasions only"],1):
        add(name,condition=lambda d,i=i:d[f"alc_{i}"].eq(1))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.data)
    assert len(frame)==94536 and frame.observed.sum()==735
    args.out.parent.mkdir(parents=True,exist_ok=True)
    summarize(frame).to_csv(args.out,index=False)

import comtradeapicall
try:
    refs = comtradeapicall.getReference(category='reporter')
    print(refs.columns.tolist())
    print(refs.iloc[0].tolist())
except Exception as e:
    print(e)

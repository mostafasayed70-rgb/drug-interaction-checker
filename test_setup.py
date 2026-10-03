import requests

response = requests.get(
    "https://api.fda.gov/drug/label.json",
    params={
        "search": 'openfda.generic_name:"ibuprofen" AND openfda.product_type:"HUMAN PRESCRIPTION DRUG"',
        "limit": 1
    },
    timeout=15
)

if response.status_code == 200:
    data = response.json()
    print("✅ الاتصال بـ openFDA ناجح!")
    
    results = data.get("results", [])
    if results:
        label = results[0]
        print(f"\nعدد الحقول في الملصق: {len(label.keys())}")
        print(f"\nالحقول المتاحة:")
        for field in label.keys():
            print(f"  - {field}")
        
        if "drug_interactions" in label:
            print("\n✅✅ لقينا قسم التداخلات!")
            text = label["drug_interactions"][0]
            print(f"\nطول النص: {len(text)} حرف")
            print(f"\nأول 800 حرف:\n{text[:800]}")
        else:
            print("\n⚠️ لسه مفيش drug_interactions")
    else:
        print("⚠️ مفيش نتائج")
else:
    print(f"❌ فشل الاتصال: {response.status_code}")
    print(response.text[:500])

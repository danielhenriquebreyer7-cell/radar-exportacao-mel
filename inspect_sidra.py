import requests
import json

def get_metadata(aggregate_id):
    url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{aggregate_id}/metadados"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(f"Aggregate: {data['id']} - {data['nome']}")
        print("\nVariables:")
        for var in data['variaveis']:
            print(f"  {var['id']}: {var['nome']}")
        
        print("\nClassifications:")
        for classif in data['classificacoes']:
            print(f"  {classif['id']}: {classif['nome']}")
            if 'categorias' in classif:
                print("    Categories (first 10):")
                for cat in classif['categorias'][:10]:
                    print(f"      {cat['id']}: {cat['nome']}")
    else:
        print(f"Error fetching metadata: {response.status_code}")

if __name__ == "__main__":
    get_metadata(74)

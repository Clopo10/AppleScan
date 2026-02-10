"""
Script pentru evaluarea modelului YOLOv8 antrenat pe setul de test.
Calculează și salvează metricile: mAP, Precision, Recall, F1-score.

"""

from ultralytics import YOLO
import json
import os

def evaluate_model():
    """
    Evaluează modelul antrenat pe setul de test și salvează metricile.
    
    Returns:
        dict: Dicționar cu metricile calculate (mAP50, mAP50-95, precision, recall, f1_score)
    """
    # Căi către model și configurare date
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_path = os.path.join(base_dir, 'models', 'mar_model_nou', 'weights', 'best.pt')
    data_yaml = os.path.join(base_dir, 'data', 'generated', 'AppleScan.yolov8', 'data.yaml')
    results_dir = os.path.join(base_dir, 'results')
    
    # Verificare existență fișiere
    if not os.path.exists(model_path):
        print(f"[EROARE] Modelul nu există la: {model_path}")
        return None
    
    if not os.path.exists(data_yaml):
        print(f"[EROARE] Fișierul data.yaml nu există la: {data_yaml}")
        return None
    
    print(f"[INFO] Încărcare model de la: {model_path}")
    model = YOLO(model_path)
    
    print(f"[INFO] Evaluare pe setul de test...")
    # Evaluare pe test set (split='test' dacă există în data.yaml, altfel folosește 'val')
    metrics = model.val(data=data_yaml, split='test')
    
    # Extragere metrici
    precision = float(metrics.box.mp)  # Mean Precision
    recall = float(metrics.box.mr)     # Mean Recall
    
    # Calculare F1-score: F1 = 2 * (precision * recall) / (precision + recall)
    if (precision + recall) > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
    else:
        f1_score = 0.0
    
    # Dicționar rezultate
    results = {
        'test_metrics': {
            'mAP50': float(metrics.box.map50),           # mAP la IoU=0.5
            'mAP50-95': float(metrics.box.map),          # mAP la IoU=0.5:0.95
            'precision': precision,                      # Precizie medie
            'recall': recall,                            # Recall mediu
            'f1_score': f1_score,                        # F1-score calculat
        },
        'model_info': {
            'model_path': model_path,
            'data_config': data_yaml,
            'evaluation_date': '12.12.2025'
        }
    }
    
    # Creare folder results dacă nu există
    os.makedirs(results_dir, exist_ok=True)
    
    # Salvare metrici în JSON
    output_path = os.path.join(results_dir, 'test_metrics.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    # Afișare rezultate
    print("\n" + "="*60)
    print("📊 REZULTATE EVALUARE PE TEST SET")
    print("="*60)
    print(f"✓ mAP50:          {results['test_metrics']['mAP50']:.4f} ({results['test_metrics']['mAP50']*100:.2f}%)")
    print(f"✓ mAP50-95:       {results['test_metrics']['mAP50-95']:.4f} ({results['test_metrics']['mAP50-95']*100:.2f}%)")
    print(f"✓ Precision:      {results['test_metrics']['precision']:.4f} ({results['test_metrics']['precision']*100:.2f}%)")
    print(f"✓ Recall:         {results['test_metrics']['recall']:.4f} ({results['test_metrics']['recall']*100:.2f}%)")
    print(f"✓ F1-score:       {results['test_metrics']['f1_score']:.4f} ({results['test_metrics']['f1_score']*100:.2f}%)")
    print("="*60)
    print(f"✓ Metrici salvate în: {output_path}")
    print("="*60)
    
    # Verificare cerințe minimale Etapa 5
    print("\n📋 VERIFICARE CERINȚE ETAPA 5:")
    
    # Pentru detecție obiect, considerăm mAP50 ca "acuratețe"
    accuracy = results['test_metrics']['mAP50']
    f1 = results['test_metrics']['f1_score']
    
    if accuracy >= 0.65:
        print(f"✅ Acuratețe (mAP50): {accuracy:.2%} >= 65% (CERINȚĂ ÎNDEPLINITĂ)")
    else:
        print(f"❌ Acuratețe (mAP50): {accuracy:.2%} < 65% (CERINȚĂ NEÎNDEPLINITĂ)")
    
    if f1 >= 0.60:
        print(f"✅ F1-score: {f1:.2%} >= 60% (CERINȚĂ ÎNDEPLINITĂ)")
    else:
        print(f"❌ F1-score: {f1:.2%} < 60% (CERINȚĂ NEÎNDEPLINITĂ)")
    
    print("\n")
    
    return results

if __name__ == '__main__':
    evaluate_model()

#!/usr/bin/env python3
"""
トークン計算機能のテストスクリプト
"""
import os
import sys
import json

# Import token counter functionality
sys.path.append('/Users/raiko.funakami/GitHub/pptx-slide-translator')
from backend.token_counter import (
    TiktokenCountCallback, 
    OpenAIPricingCalculator, 
    count_tokens_text,
    calculate_openai_cost,
    estimate_translation_cost
)

def test_token_counting():
    """トークン数計算のテスト"""
    print("=== トークン数計算テスト ===")
    
    # 日本語テキストのトークン数をテスト
    japanese_text = "これはテストです。OpenAIのGPTモデルでトークン数を計算します。"
    tokens = count_tokens_text(japanese_text, "gpt-4o-mini")
    print(f"日本語テキスト: '{japanese_text}'")
    print(f"トークン数: {tokens}")
    
    # 英語テキストのトークン数をテスト
    english_text = "This is a test. We are calculating token counts with OpenAI's GPT model."
    tokens_en = count_tokens_text(english_text, "gpt-4o-mini")
    print(f"\\n英語テキスト: '{english_text}'")
    print(f"トークン数: {tokens_en}")
    
    print()

def test_cost_calculation():
    """費用計算のテスト"""
    print("=== 費用計算テスト ===")
    
    # gpt-4o-miniの費用計算
    input_tokens = 1000
    output_tokens = 500
    cost_mini = calculate_openai_cost("gpt-4o-mini", input_tokens, output_tokens)
    print(f"gpt-4o-mini: 入力{input_tokens}トークン, 出力{output_tokens}トークン")
    print(f"費用: 入力${cost_mini['input_cost']:.6f}, 出力${cost_mini['output_cost']:.6f}, 合計${cost_mini['total_cost']:.6f}")
    
    # gpt-4oの費用計算
    cost_4o = calculate_openai_cost("gpt-4o", input_tokens, output_tokens)
    print(f"\\ngpt-4o: 入力{input_tokens}トークン, 出力{output_tokens}トークン")
    print(f"費用: 入力${cost_4o['input_cost']:.6f}, 出力${cost_4o['output_cost']:.6f}, 合計${cost_4o['total_cost']:.6f}")
    
    print()

def test_translation_cost_estimation():
    """翻訳費用見積もりのテスト"""
    print("=== 翻訳費用見積もりテスト ===")
    
    # サンプルテキストリスト
    texts = [
        "このスライドは重要な情報を含んでいます。",
        "プレゼンテーションの目的は、新製品の紹介です。",
        "ターゲット市場は若年層です。",
        "販売戦略について説明します。"
    ]
    
    estimation = estimate_translation_cost(texts, "en", "gpt-4o-mini")
    print(f"テキスト数: {estimation['text_count']}")
    print(f"推定入力トークン数: {estimation['estimated_input_tokens']}")
    print(f"推定出力トークン数: {estimation['estimated_output_tokens']}")
    print(f"推定総トークン数: {estimation['estimated_total_tokens']}")
    print(f"推定費用: ${estimation['estimated_cost_breakdown']['total_cost']:.6f}")
    
    print()

def test_pricing_calculator():
    """料金計算機のテスト"""
    print("=== 料金計算機テスト ===")
    
    calculator = OpenAIPricingCalculator()
    
    # 各モデルの料金テスト
    models = ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo", "unknown-model"]
    
    for model in models:
        cost = calculator.calculate_cost(model, 1000, 500)
        print(f"{model}: ${cost['total_cost']:.6f}")
    
    print()

def test_callback_functionality():
    """コールバック機能のテスト（実際のLLM呼び出しなし）"""
    print("=== コールバック機能テスト ===")
    
    callback = TiktokenCountCallback("gpt-4o-mini")
    
    # 手動でトークン数を設定
    callback.input_tokens = 1500
    callback.output_tokens = 800
    
    metrics = callback.get_metrics()
    print("シミュレートされたメトリクス:")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    
    print()

def main():
    """メイン関数"""
    print("PPTXスライド翻訳サービス - トークン計算機能テスト")
    print("=" * 50)
    
    try:
        test_token_counting()
        test_cost_calculation()
        test_translation_cost_estimation()
        test_pricing_calculator()
        test_callback_functionality()
        
        print("✅ すべてのテストが正常に完了しました！")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
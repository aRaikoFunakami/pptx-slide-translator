import React from 'react';
import { MonthlyCost } from '../../types';

interface MonthlyCostCardProps {
  monthlyCost: MonthlyCost;
}

export const MonthlyCostCard: React.FC<MonthlyCostCardProps> = ({ monthlyCost }) => {
  return (
    <div className="monthly-cost-card">
      <h3>📊 今月の翻訳コスト</h3>
      <div className="cost-summary">
        <div className="cost-item">
          <span className="cost-label">対象月:</span>
          <span className="cost-value">{monthlyCost.current_month}</span>
        </div>
        <div className="cost-item highlight">
          <span className="cost-label">累計費用:</span>
          <span className="cost-value">${monthlyCost.total_cost_usd.toFixed(6)}</span>
        </div>
        <div className="cost-item">
          <span className="cost-label">累計トークン:</span>
          <span className="cost-value">{monthlyCost.total_tokens.toLocaleString()}</span>
        </div>
        <div className="cost-item">
          <span className="cost-label">翻訳回数:</span>
          <span className="cost-value">{monthlyCost.total_transactions.toLocaleString()} 回</span>
        </div>
      </div>
    </div>
  );
};

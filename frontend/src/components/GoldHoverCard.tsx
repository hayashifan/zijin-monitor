import React, { useState } from 'react';
import CommodityCard from './CommodityCard';
import GoldVolatilityCard from './GoldVolatilityCard';
import { CommodityPrice, GoldVolatility } from '../types';

interface Props {
  data: CommodityPrice | null;
  loading: boolean;
  volatility: GoldVolatility | null;
}

const GoldHoverCard = React.memo(function GoldHoverCard({ data, loading, volatility }: Props) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      className="gold-hover-wrap"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <CommodityCard data={data} type="gold" loading={loading} />
      <div className={`gold-hover-overlay ${hovered ? 'gold-hover-visible' : ''}`}>
        <GoldVolatilityCard data={volatility} loading={loading} />
      </div>
    </div>
  );
});

export default GoldHoverCard;

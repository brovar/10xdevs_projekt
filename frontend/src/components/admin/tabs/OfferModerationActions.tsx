import React from 'react';
import { OfferSummaryDTO, OfferStatus } from '../../../types/api';

interface OfferModerationActionsProps {
  offer: OfferSummaryDTO;
  onModerate: (offerId: string) => void;
  onUnmoderate: (offerId: string) => void;
}

const OfferModerationActions: React.FC<OfferModerationActionsProps> = ({
  offer,
  onModerate,
  onUnmoderate
}) => {
  const isModerated = offer.status === OfferStatus.MODERATED;
  
  // Determine if offer can be moderated or unmoderated based on status
  const canBeModerated = !isModerated && 
    offer.status !== OfferStatus.DELETED && 
    offer.status !== OfferStatus.SOLD;
  
  const canBeUnmoderated = isModerated;

  return (
    <div className="d-flex gap-2">
      {/* Moderate button */}
      {canBeModerated && (
        <button
          type="button"
          className="btn btn-sm btn-primary"
          onClick={() => onModerate(offer.id)}
          aria-label={`Moderuj ofertę "${offer.title}"`}
        >
          <i className="bi bi-check2-circle me-1"></i>
          Moderuj
        </button>
      )}
      
      {/* Unmoderate button */}
      {canBeUnmoderated && (
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          onClick={() => onUnmoderate(offer.id)}
          aria-label={`Odmoderuj ofertę "${offer.title}"`}
        >
          <i className="bi bi-arrow-counterclockwise me-1"></i>
          Odmoderuj
        </button>
      )}

      {/* If offer can't be moderated or unmoderated, show disabled state */}
      {!canBeModerated && !canBeUnmoderated && (
        <button
          type="button"
          className="btn btn-sm btn-outline-secondary"
          disabled
          aria-label="Cannot moderate this offer"
        >
          No actions
        </button>
      )}
    </div>
  );
};

export default OfferModerationActions; 
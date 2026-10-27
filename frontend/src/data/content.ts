export interface TechnicalContent {
  title: string;
  text: string;
  source: string;
  reviewedAt: string;
  validated: boolean;
}

// Keys are the exact indices from the versioned model's classes.json.
// Populate only after the partner has reviewed the content and its association.
export const technicalContent: Partial<Record<number, TechnicalContent>> = {};

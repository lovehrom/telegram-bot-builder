/**
 * Centralized validation utilities for flows
 */

/**
 * Validate block configuration before saving
 */
export function validateBlockConfig(blockType: string, config: Record<string, any>, label?: string): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Check label
  if (label !== undefined) {
    if (typeof label !== 'string' || !label.trim()) {
      errors.push('Block label cannot be empty');
    }
  }

  // Validate payment block
  if (blockType === 'create_payment') {
    if (!config.amount) {
      errors.push('create_payment block requires "amount" in config');
    } else if (typeof config.amount !== 'number') {
      errors.push('"amount" must be a number');
    } else if (config.amount <= 0) {
      errors.push('"amount" must be greater than 0');
    }
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Validate connection before creating
 */
export function validateConnection(
  fromBlockId: number,
  toBlockId: number,
  flowId: number,
  existingBlocks: number[]
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  // Check blocks exist
  if (!existingBlocks.includes(fromBlockId)) {
    errors.push(`Block ${fromBlockId} does not exist`);
  }

  if (!existingBlocks.includes(toBlockId)) {
    errors.push(`Block ${toBlockId} does not exist`);
  }

  // Check self-connection
  if (fromBlockId === toBlockId) {
    errors.push('Cannot create connection to the same block');
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

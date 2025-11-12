/**
 * Simple localStorage service for persisting UI state
 */

const StorageService = {
    /**
     * Get a value from localStorage
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if key doesn't exist
     * @returns {*} Parsed value or default
     */
    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('StorageService.get error:', error);
            return defaultValue;
        }
    },

    /**
     * Set a value in localStorage
     * @param {string} key - Storage key
     * @param {*} value - Value to store (will be JSON stringified)
     */
    set: function(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('StorageService.set error:', error);
        }
    },

    /**
     * Remove a key from localStorage
     * @param {string} key - Storage key to remove
     */
    remove: function(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('StorageService.remove error:', error);
        }
    }
};

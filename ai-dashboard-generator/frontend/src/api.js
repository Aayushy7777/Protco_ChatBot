const BASE_URL = 'http://localhost:8010'; // Backend server

export async function uploadFiles(files) {
    const allFiles = [];
    const errors = [];
    
    // Upload files one at a time
    for (let file of files) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ errors: ["Unknown error"] }));
                errors.push(errorData.errors?.[0] || `Failed to upload ${file.name}`);
                continue;
            }
            const result = await response.json();
            if (result.success && result.files) {
                allFiles.push(...result.files);
            } else if (result.errors) {
                errors.push(...result.errors);
            }
        } catch (error) {
            errors.push(`Error uploading ${file.name}: ${error.message}`);
        }
    }
    
    return {
        success: allFiles.length > 0,
        files: allFiles,
        errors: errors,
    };
}

export async function sendChat({ message, activeFile, allFiles, history }) {
    try {
        const response = await fetch(`${BASE_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message,
                active_file: activeFile,
                all_files: allFiles,
                history,
            }),
        });
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: "Unknown chat error" }));
            throw new Error(errorData.detail || 'Chat request failed');
        }
        return response.json();
    } catch (error) {
        console.error("Chat error:", error);
        throw error;
    }
}

export async function generateDashboard(filename) {
    try {
        const response = await fetch(`${BASE_URL}/api/profile`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: "Dashboard generation failed" }));
            throw new Error(errorData.error || 'Profile not available');
        }
        return response.json();
    } catch (error) {
        console.error("Dashboard generation error:", error);
        throw error;
    }
}

export async function checkHealth() {
    try {
        const response = await fetch(`${BASE_URL}/api/health`);
        if (!response.ok) {
            return { status: 'error', ollama: false };
        }
        return response.json();
    } catch (error) {
        return { status: 'error', ollama: false };
    }
}

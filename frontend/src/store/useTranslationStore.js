import { create } from 'zustand';
import axios from 'axios';

const API_BASE_URL = "http://localhost:8000";

export const useTranslationStore = create((set, get) => ({
  projects: [],
  currentProject: null,
  segments: [],
  glossaryTerms: [],
  loading: false,
  error: null,

  fetchProjects: async () => {
    set({ loading: true });
    try {
      const response = await axios.get(`${API_BASE_URL}/projects`);
      set({ projects: response.data, loading: false });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  fetchProjectSegments: async (projectId) => {
    set({ loading: true });
    try {
      const response = await axios.get(`${API_BASE_URL}/review/project/${projectId}/segments`);
      set({ segments: response.data, loading: false });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  approveSegment: async (segmentId, approvedText) => {
    try {
      await axios.post(`${API_BASE_URL}/review/segments/${segmentId}/approve`, {
        approved_translation: approvedText,
        reviewer_name: "Lead Linguist"
      });
      // Update local state instantly
      set((state) => ({
        segments: state.segments.map((seg) =>
          seg.id === segmentId
            ? { ...seg, translated_text: approvedText, status: 'accepted' }
            : seg
        ),
      }));
    } catch (err) {
      set({ error: err.message });
    }
  }
}));

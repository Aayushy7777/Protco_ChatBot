import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useChatStore = create(
  persist(
    (set, get) => ({
      conversations: {},
      activeConversation: null,
      
      createConversation: (fileId) => {
        const id = `conv_${Date.now()}`;
        set((state) => ({
          conversations: {
            ...state.conversations,
            [id]: {
              id,
              fileId,
              title: 'New Chat',
              messages: [
                {
                  role: 'assistant',
                  content: '👋 Welcome! I\'m your AI data analyst. Upload a CSV and ask questions about your data.',
                  timestamp: Date.now(),
                }
              ],
              createdAt: Date.now(),
              updatedAt: Date.now(),
            }
          },
          activeConversation: id,
        }));
        return id;
      },
      
      addMessage: (conversationId, message) => {
        set((state) => {
          const conv = state.conversations[conversationId];
          if (!conv) return state;
          return {
            conversations: {
              ...state.conversations,
              [conversationId]: {
                ...conv,
                messages: [...conv.messages, {
                  ...message,
                  timestamp: Date.now(),
                }],
                updatedAt: Date.now(),
              }
            }
          };
        });
      },
      
      updateLastMessage: (conversationId, content) => {
        set((state) => {
          const conv = state.conversations[conversationId];
          if (!conv || conv.messages.length === 0) return state;
          const messages = [...conv.messages];
          messages[messages.length - 1].content = content;
          return {
            conversations: {
              ...state.conversations,
              [conversationId]: {
                ...conv,
                messages,
                updatedAt: Date.now(),
              }
            }
          };
        });
      },
      
      deleteConversation: (conversationId) => {
        set((state) => {
          const { [conversationId]: removed, ...rest } = state.conversations;
          return {
            conversations: rest,
            activeConversation: state.activeConversation === conversationId ? null : state.activeConversation,
          };
        });
      },
      
      setActiveConversation: (conversationId) => {
        set({ activeConversation: conversationId });
      },
      
      updateConversationTitle: (conversationId, title) => {
        set((state) => ({
          conversations: {
            ...state.conversations,
            [conversationId]: {
              ...state.conversations[conversationId],
              title,
              updatedAt: Date.now(),
            }
          }
        }));
      },
      
      clearAll: () => {
        set({ conversations: {}, activeConversation: null });
      },
    }),
    {
      name: 'chat-store',
      version: 1,
    }
  )
);

import React from 'react';
import { motion } from 'framer-motion';

const LoadingIndicator = () => {
  const containerVariants = {
    initial: {
      transition: {
        staggerChildren: 0.2,
      },
    },
    animate: {
      transition: {
        staggerChildren: 0.2,
      },
    },
  };

  const dotVariants = {
    initial: {
      y: '0%',
    },
    animate: {
      y: '100%',
    },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="initial"
      animate="animate"
      style={{
        width: '2rem',
        height: '2rem',
        display: 'flex',
        justifyContent: 'space-around',
        alignItems: 'center',
        padding: '0.5rem',
      }}
      className="bg-slate-700 rounded-full"
    >
      <motion.span
        style={{
          display: 'block',
          width: '0.5rem',
          height: '0.5rem',
          backgroundColor: 'white',
          borderRadius: '50%',
        }}
        variants={dotVariants}
        transition={{
          duration: 0.5,
          repeat: Infinity,
          repeatType: 'reverse',
          ease: 'easeInOut',
        }}
      />
      <motion.span
        style={{
          display: 'block',
          width: '0.5rem',
          height: '0.5rem',
          backgroundColor: 'white',
          borderRadius: '50%',
        }}
        variants={dotVariants}
        transition={{
          duration: 0.5,
          repeat: Infinity,
          repeatType: 'reverse',
          ease: 'easeInOut',
          delay: 0.2,
        }}
      />
      <motion.span
        style={{
          display: 'block',
          width: '0.5rem',
          height: '0.5rem',
          backgroundColor: 'white',
          borderRadius: '50%',
        }}
        variants={dotVariants}
        transition={{
          duration: 0.5,
          repeat: Infinity,
          repeatType: 'reverse',
          ease: 'easeInOut',
          delay: 0.4,
        }}
      />
    </motion.div>
  );
};

export default LoadingIndicator;

# Predict and inverse transform back to original scale
predicted_data = model.predict(x_test)
predicted_data = scaler.inverse_transform(predicted_data)
y_test_original = scaler.inverse_transform(y_test.reshape(-1, 1))

# Evaluate the model
mse = mean_squared_error(y_test_original, predicted_data)
print(f'Mean Squared Error: {mse}')


# Plot the results
plt.plot(y_test_original, label='Actual')
plt.plot(predicted_data, label='Predicted')
plt.legend()
plt.show()

